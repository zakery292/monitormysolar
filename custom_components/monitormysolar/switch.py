import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from homeassistant.helpers.event import (
    async_track_state_change_event,
)
from homeassistant.const import (
    STATE_UNKNOWN,
)
from .const import DOMAIN, ENTITIES, FIRMWARE_CODES
from .coordinator import MonitorMySolarEntry
from .entity import MonitorMySolarEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry: MonitorMySolarEntry, async_add_entities):
    coordinator = entry.runtime_data
    inverter_brand = coordinator.inverter_brand
    firmware_code = coordinator.firmware_code
    brand_entities = ENTITIES.get(inverter_brand, {})
    switch_config = brand_entities.get("switch", {})
    device_type = FIRMWARE_CODES.get(firmware_code, {}).get("Device_Type", "")

    entities = []
    for bank_name, switches in switch_config.items():
        for switch in switches:
            allowed_device_types = switch.get("allowed_device_types", [])
            if not allowed_device_types or device_type in allowed_device_types:
                try:
                    entities.append(
                        InverterSwitch(switch, hass, entry, bank_name)
                    )
                except Exception as e:
                    _LOGGER.error(f"Error setting up switch {switch}: {e}")

    async_add_entities(entities, True)

class InverterSwitch(MonitorMySolarEntity, SwitchEntity):
    def __init__(self, entity_info, hass, entry: MonitorMySolarEntry, bank_name):
        """Initialize the switch."""
        _LOGGER.debug(f"Initializing switch with info: {entity_info}")
        self.coordinator = entry.runtime_data
        self.entity_info = entity_info
        self._name = entity_info["name"]
        self._unique_id = f"{entry.entry_id}_{entity_info['unique_id']}".lower()
        self._state = False
        self._dongle_id = self.coordinator.dongle_id
        self._device_id = self.coordinator.dongle_id
        self._entity_type = entity_info["unique_id"]
        self._bank_name = bank_name
        self.entity_id = f"switch.{self._device_id}_{self._entity_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._previous_state = None

        super().__init__(self.coordinator)

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def is_on(self):
        return self._state

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._dongle_id)},
            "name": f"Inverter {self._dongle_id}",
            "manufacturer": f"{self._manufacturer}",
        }

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        mqtt_handler = self.coordinator.mqtt_handler
        if mqtt_handler is not None:
            self._previous_state = self._state
            self._state = True  # Optimistically update the state
            self.async_write_ha_state()
            _LOGGER.info(f"Setting Switch on value for {self.entity_id}")
            success = await mqtt_handler.send_update(
                self._dongle_id, self.entity_info["unique_id"], 1, self
            )
            if not success:
                self.revert_state()
        else:
            _LOGGER.error("MQTT Handler is not initialized")

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        mqtt_handler = self.coordinator.mqtt_handler
        if mqtt_handler is not None:
            self._previous_state = self._state  # Save the current state before changing
            self._state = False  # Optimistically update the state in HA
            self.async_write_ha_state()  # Update HA state immediately
            _LOGGER.info(f"Setting Switch off value for {self.entity_id}")
            success = await mqtt_handler.send_update(
                self._dongle_id, self.entity_info["unique_id"], 0, self
            )
            if not success:
                self.revert_state()
        else:
            _LOGGER.error("MQTT Handler is not initialized")

    def revert_state(self):
        """Revert to the previous state."""
        if self._previous_state is not None:
            self._state = self._previous_state
            self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""

        # This method is called by your DataUpdateCoordinator when a successful update runs.
        if self.entity_id in self.coordinator.entities:
            value = self.coordinator.entities[self.entity_id]
            if value is not None:
                self._state = bool(value)
                #_LOGGER.debug(f"Switch {self.entity_id} state updated to {value}")
                # Schedule state update on the main thread
                self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
