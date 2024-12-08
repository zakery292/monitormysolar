"""Battery status binary sensors."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import callback
from .const import DOMAIN, BATTERY_STATUS_MAP, ENTITIES


import logging
_LOGGER = logging.getLogger(__name__)
async def async_setup_entry(hass, entry, async_add_entities):
    """Set up binary sensors based on a config entry."""
    inverter_brand = entry.data.get("inverter_brand")
    dongle_id = entry.data.get("dongle_id").lower().replace("-", "_")
    
    brand_entities = ENTITIES.get(inverter_brand, {})
    sensors_config = brand_entities.get("binary_sensor", {})  # We're still using the sensor config
    
    entities = []
    
    for bank_name, sensors in sensors_config.items():
        for sensor in sensors:
            if bank_name == "battery":
                entities.append(
                    BatteryStatusBinarySensor(sensor, hass, entry, dongle_id)
                )
    
    async_add_entities(entities, True)


class BatteryStatusBinarySensor(BinarySensorEntity):
    """Binary sensor for battery charge/discharge status."""

    def __init__(self, sensor_info, hass, entry, dongle_id):
        """Initialize the binary sensor."""
        self.sensor_info = sensor_info
        self._name = sensor_info["name"]
        self._unique_id = f"{entry.entry_id}_{sensor_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = dongle_id.lower().replace("-", "_")
        self._status_type = sensor_info.get("status_type")
        self.entity_id = f"binary_sensor.{self._dongle_id}_{sensor_info['unique_id']}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._parent_sensor = sensor_info.get("parent_sensor")

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
    def state(self):
        """Return the state of the binary sensor."""
        return "Allowed" if self._state else "Forbidden"

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
        event_entity_id = event.data.get("entity").lower().replace("-", "_")
        value = event.data.get("value")
        _LOGGER.debug(f"Binary sensor {self.entity_id} received event: {event_entity_id} with value {value}")

        # Check if this update is for our parent sensor (BatStatusINV)
        if event_entity_id.endswith(self._parent_sensor.lower()):
            try:
                status_value = str(int(value)).zfill(2)
                if status_value in BATTERY_STATUS_MAP:
                    self._state = BATTERY_STATUS_MAP[status_value][self._status_type]
                    self.async_write_ha_state()
            except ValueError:
                _LOGGER.debug(f"Invalid battery status value: {value}")

    async def async_added_to_hass(self):
        """Subscribe to events when added to hass."""
        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_sensor_updated", self._handle_event)
        )
        _LOGGER.debug(f"Binary sensor {self.entity_id} subscribed to event")