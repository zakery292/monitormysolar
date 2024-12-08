import logging
from homeassistant.components.select import SelectEntity
from homeassistant.core import callback
from .const import DOMAIN, ENTITIES
from . import MonitorMySolarEntry

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    inverter_brand = entry.data.get("inverter_brand")
    dongle_id = entry.data.get("dongle_id").lower().replace("-", "_")
    brand_entities = ENTITIES.get(inverter_brand, {})
    select_config = brand_entities.get("select", {})

    entities = []
    for bank_name, selects in select_config.items():
        for select in selects:
            try:
                if bank_name == "holdbank6":
                    entities.append(QuickChargeDurationSelect(select, hass, entry, dongle_id, bank_name))
                else:
                    entities.append(InverterSelect(select, hass, entry, dongle_id))
            except Exception as e:
                _LOGGER.error(f"Error setting up select {select}: {e}")

    async_add_entities(entities, True)

class InverterSelect(SelectEntity):
    def __init__(self, entity_info, hass, entry: MonitorMySolarEntry, dongle_id):
        """Initialize the select entity."""
        _LOGGER.debug(f"Initializing select with info: {entity_info}")
        self.entity_info = entity_info
        self._name = entity_info["name"]
        self._unique_id = f"{entry.entry_id}_{entity_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = dongle_id.lower().replace("-", "_")
        self._device_id = dongle_id.lower().replace("-", "_")
        self._entity_type = entity_info["unique_id"]
        self.entity_id = f"select.{self._device_id}_{self._entity_type.lower()}"
        self.hass = hass
        self._options = entity_info["options"]
        self._manufacturer = entry.data.get("inverter_brand")
        self.coordinator = entry.runtime_data

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def current_option(self):
        return self._state

    @property
    def options(self):
        return self._options

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._dongle_id)},
            "name": f"Inverter {self._dongle_id}",
            "manufacturer": f"{self._manufacturer}",
        }

    async def async_select_option(self, option):
        """Update the select option."""
        _LOGGER.info(f"Setting select option for {self.entity_id} to {option}")
        self._state = option
        self.async_write_ha_state



        bit_value = self._options.index(option)
        _LOGGER.info(f"Setting Select value for {self.entity_id} to {option}")
        await self.coordinator.mqtt_handler.send_update(
            self._dongle_id.replace("_", "-"),
            self.entity_info["unique_id"],
            bit_value,
            self,
        )

    def revert_state(self):
        """Revert to the previous state."""
        _LOGGER.info(f"Reverting state for {self.entity_id} to {self._state}")
        # Schedule state revert on the main thread
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)

    @callback
    def _handle_event(self, event):
        """Handle the event."""
        _LOGGER.debug(f"Handling event for select {self.entity_id}: {event.data}")
        event_entity_id = event.data.get("entity").lower().replace("-", "_")
        if event_entity_id == self.entity_id:
            value = event.data.get("value")
            _LOGGER.debug(f"Received event for select {self.entity_id}: {value}")
            if value is not None:
                self._state = (
                    self._options[value]
                    if isinstance(value, int) and value < len(self._options)
                    else value
                )
                _LOGGER.debug(f"Select {self.entity_id} state updated to {self._state}")
                # Schedule state update on the main thread
                self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
       # _LOGGER.debug(f"Select {self.entity_id} added to hass")
        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_select_updated", self._handle_event)
        )
        #_LOGGER.debug(f"Select {self.entity_id} subscribed to event")


class QuickChargeDurationSelect(SelectEntity):
    def __init__(self, entity_info, hass, entry, dongle_id, bank_name):
        """Initialize the select entity."""
        self.entity_info = entity_info
        self._attr_name = entity_info["name"]
        self._attr_unique_id = f"{entry.entry_id}_{entity_info['unique_id']}".lower()
        self._attr_options = entity_info["options"]
        self._attr_current_option = self._attr_options[0]  # Default to first option
        self._dongle_id = dongle_id.lower().replace("-", "_")
        self._entity_type = entity_info["unique_id"]
        self.entity_id = f"select.{self._dongle_id}_{self._entity_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._additional_payload = entity_info.get("additional_payload")

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        mqtt_handler = self.coordinator.mqtt_handler
        if mqtt_handler is not None:
            # Prepare the payload dictionary
            payload_dict = {
                self._entity_type: option
            }
            
            # Add additional payload if configured
            if self._additional_payload:
                value_map = self._additional_payload.get("value_map", {})
                additional_value = value_map.get(option, value_map.get("default"))
                if additional_value is not None:
                    payload_dict[self._additional_payload["key"]] = additional_value

            # Send the multiple updates via MQTT
            await mqtt_handler.send_multiple_updates(
                self._dongle_id.replace("_", "-"),
                payload_dict,
                self,
            )
            
            self._attr_current_option = option
            self.async_write_ha_state()
        else:
            _LOGGER.error("MQTT Handler is not initialized")

    @callback
    def _handle_event(self, event):
        """Handle the event."""
        event_entity_id = event.data.get("entity").lower().replace("-", "_")
        if event_entity_id == self.entity_id:
            value = event.data.get("value")
            if value in self._attr_options:
                self._attr_current_option = value
                self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Subscribe to events when added to hass."""
        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_select_updated", self._handle_event)
        )