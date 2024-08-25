from datetime import datetime
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from .const import DOMAIN, ENTITIES, FIRMWARE_CODES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    inverter_brand = entry.data.get("inverter_brand")
    dongle_id = entry.data.get("dongle_id").lower().replace("-", "_")
    firmware_code = entry.data.get("firmware_code")
    device_type = FIRMWARE_CODES.get(firmware_code, {}).get("Device_Type", "")

    brand_entities = ENTITIES.get(inverter_brand, {})
    sensors_config = brand_entities.get("sensor", {})

    entities = []
    for bank_name, sensors in sensors_config.items():
        for sensor in sensors:
            allowed_device_types = sensor.get("allowed_device_types", [])
            if not allowed_device_types or device_type in allowed_device_types:
                try:
                    entities.append(
                        InverterSensor(sensor, hass, entry, dongle_id, bank_name)
                    )
                except Exception as e:
                    _LOGGER.error(f"Error setting up sensor {sensor}: {e}")

    async_add_entities(entities, True)


class InverterSensor(SensorEntity):
    def __init__(self, sensor_info, hass, entry, dongle_id, bank_name):
        """Initialize the sensor."""
        _LOGGER.debug(f"Initializing sensor with info: {sensor_info}")
        self.sensor_info = sensor_info
        self._name = sensor_info["name"]
        self._unique_id = f"{entry.entry_id}_{sensor_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = dongle_id.lower().replace("-", "_")
        self._device_id = dongle_id.lower().replace("-", "_")
        self._sensor_type = sensor_info["unique_id"]
        self._bank_name = bank_name
        self.entity_id = f"sensor.{self._device_id}_{self._sensor_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")

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

    @property
    def device_class(self):
        return self.sensor_info.get("device_class")

    @property
    def last_reset(self):
        """Return the time when the sensor was last reset (midnight)."""
        if self.state_class == "total":
            return datetime.min
        return None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._dongle_id)},
            "name": f"Inverter {self._dongle_id}",
            "manufacturer": f"{self._manufacturer}",
        }

    @callback
    def _handle_event(self, event):
        """Handle the event."""
        _LOGGER.debug(f"Handling event for sensor {self.entity_id}: {event.data}")
        event_entity_id = event.data.get("entity").lower().replace("-", "_")
        if event_entity_id == self.entity_id:
            value = event.data.get("value")
            _LOGGER.debug(f"Received event for sensor {self.entity_id}: {value}")
            if value is not None:
                self._state = (
                    round(value, 2) if isinstance(value, (float, int)) else value
                )
                _LOGGER.debug(f"Sensor {self.entity_id} state updated to {value}")
                self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        _LOGGER.debug(f"Sensor {self.entity_id} added to hass")
        self.hass.bus.async_listen(f"{DOMAIN}_sensor_updated", self._handle_event)
        _LOGGER.debug(f"Sensor {self.entity_id} subscribed to event")
