# sensor.py
import logging
from homeassistant.components.sensor import SensorEntity
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
        self._name = sensor_info["name"]
        self._unique_id = f"{entry.entry_id}_{sensor_info['unique_id']}"
        self._state = None
        self._dongle_id = dongle_id
        self.hass = hass

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

    async def async_update(self):
        # Here you could add code to fetch the latest state from the device if needed
        pass

    async def set_state(self, value):
        """Set the state of the sensor."""
        self._state = value
        await self.async_update_ha_state()
