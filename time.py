# time.py
import logging
from homeassistant.components.time import TimeEntity
from .const import DOMAIN, SENSORS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    inverter_brand = entry.data.get("inverter_brand")
    dongle_id = entry.data.get("dongle_id")
    times = [sensor for sensor in SENSORS.get(inverter_brand, []) if sensor["type"] == "time"]

    entities = [InverterTime(sensor, entry, dongle_id, hass) for sensor in times]
    async_add_entities(entities, True)

class InverterTime(TimeEntity):
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

    async def async_update(self):
        # Here you could add code to fetch the latest state from the device if needed
        pass

    async def set_state(self, hh, mm):
        """Set the state of the time entity."""
        self._state = f"{hh:02}:{mm:02}"
        await self.async_update_ha_state()
