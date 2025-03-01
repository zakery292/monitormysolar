from homeassistant.components.number import NumberEntity
from homeassistant.core import callback
import json
from homeassistant.helpers.event import (
    async_track_state_change_event,
)
from homeassistant.const import (
    STATE_UNKNOWN,
)
from .const import DOMAIN, ENTITIES, LOGGER
from .coordinator import MonitorMySolarEntry
from .entity import MonitorMySolarEntity

async def async_setup_entry(hass, entry: MonitorMySolarEntry, async_add_entities):
    coordinator = entry.runtime_data
    inverter_brand = coordinator.inverter_brand
    brand_entities = ENTITIES.get(inverter_brand, {})
    number_config = brand_entities.get("number", {})

    entities = []
    for bank_name, numbers in number_config.items():
        for number in numbers:
            try:
                entities.append(
                    InverterNumber(number, hass, entry, bank_name)
                )
            except Exception as e:
                LOGGER.error(f"Error setting up number {number}: {e}")

    async_add_entities(entities, True)

class InverterNumber(MonitorMySolarEntity, NumberEntity):
    def __init__(self, entity_info, hass, entry: MonitorMySolarEntry, bank_name):
        """Initialize the number."""
        self.coordinator = entry.runtime_data
        self.entity_info = entity_info
        self._attr_name = entity_info["name"]
        self._attr_unique_id = f"{entry.entry_id}_{entity_info['unique_id']}".lower()
        self._attr_native_value = 0
        self._dongle_id = self.coordinator.dongle_id
        self._device_id = self.coordinator.dongle_id
        self._entity_type = entity_info["unique_id"]
        self._bank_name = bank_name
        self.entity_id = f"number.{self._device_id}_{self._entity_type.lower()}"
        self.hass = hass
        self._attr_native_min_value = entity_info.get("min", None)
        self._attr_native_max_value = entity_info.get("max", None)
        self._attr_mode = entity_info.get("mode", "auto")
        self._attr_native_unit_of_measurement = entity_info.get("native_unit_of_measurement", None)
        self._attr_device_class = entity_info.get("device_class", None)
        self._manufacturer = entry.data.get("inverter_brand")
        self._previous_value = self._attr_native_value  # Track the previous value for revert
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._dongle_id)},
            "name": f"Inverter {self._dongle_id}",
            "manufacturer": f"{self._manufacturer}",
        }

        super().__init__(self.coordinator)

    async def async_set_native_value(self, value):
        """Set the number value."""
        LOGGER.debug(f"Setting value of number {self.entity_id} to {value}")
        mqtt_handler = self.coordinator.mqtt_handler
        if mqtt_handler is not None:
            # Save the current value before changing
            self._previous_value = self._attr_native_value
            # Set the new value
            self._attr_native_value = value
            self.async_write_ha_state()

            # Send the update via MQTT
            await mqtt_handler.send_update(
                self._dongle_id.replace("_", "-"),
                self.entity_info["unique_id"],
                value,
                self,
            )
        else:
            LOGGER.error("MQTT Handler is not initialized")

    def revert_state(self):
        """Revert to the previous state."""
        LOGGER.info(f"Reverting state for {self.entity_id} to {self._previous_value}")
        self._attr_native_value = self._previous_value
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""

        # This method is called by your DataUpdateCoordinator when a successful update runs.
        if self.entity_id in self.coordinator.entities:
            value = self.coordinator.entities[self.entity_id]
            if value is not None:
                self._attr_native_value = value
                self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)
