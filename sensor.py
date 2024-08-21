import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from homeassistant.helpers.event import async_call_later
from .const import DOMAIN, SENSORS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    inverter_brand = entry.data.get("inverter_brand")
    dongle_id = entry.data.get("dongle_id")
    sensors = [sensor for sensor in SENSORS.get(inverter_brand, []) if sensor["type"] == "sensor"]

    entities = [InverterSensor(sensor, entry, dongle_id, hass) for sensor in sensors]
    async_add_entities(entities, True)

class InverterSensor(SensorEntity):
    def __init__(self, sensor_info, entry, dongle_id, hass):
        self.sensor_info = sensor_info
        self._name = sensor_info["name"]
        self._unique_id = f"{entry.entry_id}_{sensor_info['unique_id']}"
        self._state = None
        self._dongle_id = dongle_id
        self.entity_id = f"sensor.{dongle_id}_{sensor_info['unique_id']}"
        self.hass = hass

    # async def async_added_to_hass(self):
    #     """Call when entity is added to hass."""
    #     _LOGGER.warning(f"Adding listener for {self.entity_id}")
    #     async_call_later(self.hass, 0, self._register_listener)

    # async def _register_listener(self, _):
    #    await self.hass.bus.async_listen(f"{DOMAIN}_sensor_updated", self._handle_event)

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._state

    @property
    def state_class(self):
        return self.sensor_info.get("state_class")

    @property
    def unit_of_measurement(self):
        return self.sensor_info.get("unit")

    @callback
    def _handle_event(self, event):
        """Handle the event."""
        _LOGGER.warning(f"Sensor {self.entity_id} received event: {event.data}")
        if event.data.get("entity") == self.entity_id:
            self._state = event.data.get("value")
            self.async_write_ha_state()

    async def async_update(self):
        """Update the sensor state."""
        _LOGGER.warning(f"Updating sensor {self.entity_id}")
