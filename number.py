# number.py
import logging
from homeassistant.components.number import NumberEntity
from .const import DOMAIN, SENSORS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    inverter_brand = entry.data.get("inverter_brand")
    sensors = SENSORS.get(inverter_brand, [])

    entities = []
    for sensor in sensors:
        if sensor["type"] == "number":
            entities.append(InverterNumber(sensor, entry))

    async_add_entities(entities, True)

class InverterNumber(NumberEntity):
    def __init__(self, sensor_info, entry):
        self._name = sensor_info["name"]
        self._unit_of_measurement = sensor_info.get("unit")
        self._unique_id = f"{entry.entry_id}_{sensor_info['unique_id']}"
        self._state = None

    @property
    def name(self):
        return self._name

    @property
    def unit_of_measurement(self):
        return self._unit_of_measurement

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def value(self):
        return self._state

    async def async_update(self):
        # Update the number state here based on received JSON data
        pass
