import logging
from homeassistant.components.number import NumberEntity
from homeassistant.core import callback
import json
from .const import DOMAIN, ENTITIES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    inverter_brand = entry.data.get("inverter_brand")
    dongle_id = entry.data.get("dongle_id").lower().replace("-", "_")
    brand_entities = ENTITIES.get(inverter_brand, {})
    number_config = brand_entities.get("number", {})

    entities = []
    for bank_name, numbers in number_config.items():
        for number in numbers:
            try:
                entities.append(
                    InverterNumber(number, hass, entry, dongle_id, bank_name)
                )
            except Exception as e:
                _LOGGER.error(f"Error setting up number {number}: {e}")

    async_add_entities(entities, True)


class InverterNumber(NumberEntity):
    def __init__(self, entity_info, hass, entry, dongle_id, bank_name):
        """Initialize the number."""
        _LOGGER.debug(f"Initializing number with info: {entity_info}")
        self.entity_info = entity_info
        self._name = entity_info["name"]
        self._unique_id = f"{entry.entry_id}_{entity_info['unique_id']}".lower()
        self._value = 0
        self._dongle_id = dongle_id.lower().replace("-", "_")
        self._device_id = dongle_id.lower().replace("-", "_")
        self._entity_type = entity_info["unique_id"]
        self._bank_name = bank_name
        self.entity_id = f"number.{self._device_id}_{self._entity_type.lower()}"
        self.hass = hass
        self._min_value = entity_info.get("min", None)
        self._max_value = entity_info.get("max", None)
        self._mode = entity_info.get("mode", "auto")
        self._native_unit_of_measurement = entity_info.get("native_unit_of_measurement", None)
        self._device_class = entity_info.get("device_class", None)
        self._manufacturer = entry.data.get("inverter_brand")

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def native_value(self):
        return self._value

    @property
    def min_value(self):
        return self._min_value

    @property
    def max_value(self):
        return self._max_value

    @property
    def mode(self):
        return self._mode

    @property
    def native_unit_of_measurement(self):
        return self._native_unit_of_measurement

    @property
    def device_class(self):
        return self._device_class

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._dongle_id)},
            "name": f"Inverter {self._dongle_id}",
            "manufacturer": f"{self._manufacturer}",
        }

    async def async_set_value(self, value):
        """Set the number value."""
        _LOGGER.debug(f"Setting value of number {self.entity_id} to {value}")
        mqtt_handler = self.hass.data[DOMAIN].get("mqtt_handler")
        if mqtt_handler is not None:
            await mqtt_handler.send_update(
                self._dongle_id.replace("_", "-"),
                self.entity_info["unique_id"],
                value,
                self,
            )
        else:
            _LOGGER.error("MQTT Handler is not initialized")

    @callback
    def _handle_event(self, event):
        """Handle the event."""
        _LOGGER.debug(f"Handling event for number {self.entity_id}: {event.data}")
        event_entity_id = event.data.get("entity").lower().replace("-", "_")
        if event_entity_id == self.entity_id:
            value = event.data.get("value")
            _LOGGER.debug(f"Received event for number {self.entity_id}: {value}")
            if value is not None:
                self._value = value
                _LOGGER.debug(f"Number {self.entity_id} value updated to {value}")
                self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        _LOGGER.debug(f"Number {self.entity_id} added to hass")
        self.hass.bus.async_listen(f"{DOMAIN}_number_updated", self._handle_event)
        _LOGGER.debug(f"Number {self.entity_id} subscribed to event")

    async def async_will_remove_from_hass(self):
        """Unsubscribe from events when removed."""
        _LOGGER.debug(f"Number {self.entity_id} will be removed from hass")
        self.hass.bus.async_remove_listener(
            f"{DOMAIN}_number_updated", self._handle_event
        )
