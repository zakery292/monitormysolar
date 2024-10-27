from datetime import datetime
import logging
import json
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from .const import DOMAIN, ENTITIES, FIRMWARE_CODES
from homeassistant.const import (
    CONF_MODE,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    inverter_brand = entry.data.get("inverter_brand")
    dongle_id = entry.data.get("dongle_id").lower().replace("-", "_")
    firmware_code = entry.data.get("firmware_code")

    brand_entities = ENTITIES.get(inverter_brand, {})
    sensors_config = brand_entities.get("sensor", {})
    
    entities = []
    
    # Loop through the sensors in the configuration
    for bank_name, sensors in sensors_config.items():
        for sensor in sensors:
            allowed_firmware_codes = sensor.get("allowed_firmware_codes", [])
            if not allowed_firmware_codes or firmware_code in allowed_firmware_codes:
                try:
                    # Check if the sensor is of type 'status' to create the StatusSensor class
                    if bank_name == "status":
                        entities.append(
                            StatusSensor(sensor, hass, entry, dongle_id, bank_name),
                        )
                    elif bank_name == "powerflow":
                        entities.append(
                            PowerFlowSensor(sensor, hass, entry, dongle_id, bank_name)
                        )
                    elif bank_name == "timestamp":
                        entities.append(
                            BankUpdateSensor(sensor, hass, entry, dongle_id, bank_name)
                        )
                    else:
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
        return self.sensor_info.get("unit_of_measurement") 

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
            if value is not None:
                if self._sensor_type == "RunningTime" and isinstance(value, (float, int)):
                    # Convert seconds to HH:MM:SS format
                    seconds = int(value)
                    hours, remainder = divmod(seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    self._state = f"{hours:02}:{minutes:02}:{seconds:02}"
                else:
                    self._state = (
                        round(value, 2) if isinstance(value, (float, int)) else value
                    )
                _LOGGER.debug(f"Sensor {self.entity_id} state updated to {self._state}")
                self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        """Unsubscribe from events when removed."""
        _LOGGER.debug(f"Sensor {self.entity_id} will be removed from hass")
        self.hass.bus._async_remove_listener(f"{DOMAIN}_sensor_updated", self._handle_event)

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        _LOGGER.debug(f"Sensor {self.entity_id} added to hass")
        self.hass.bus.async_listen(f"{DOMAIN}_sensor_updated", self._handle_event)
        _LOGGER.debug(f"Sensor {self.entity_id} subscribed to event")



class StatusSensor(SensorEntity):
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
        self._expected_attributes = sensor_info.get("attributes", [])

        # Initialize attributes with default values
        self._attributes = {attr: "unknown" for attr in self._expected_attributes}

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
    def extra_state_attributes(self):
        return self._attributes

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
            _LOGGER.debug(f'Value received: {value}')
            if isinstance(value, dict):
                # Extract the 'uptime' for the sensor's state
                self._state = value.get("uptime")
                _LOGGER.debug(f'State updated to: {self._state}')
                
                # Update the sensor's attributes based on the expected attributes list
                for attr in self._expected_attributes:
                    self._attributes[attr] = value.get(attr, "unknown")
                
                _LOGGER.debug(f'Attributes updated to: {self._attributes}')
                
                self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        """Unsubscribe from events when removed."""
        _LOGGER.debug(f"Sensor {self.entity_id} will be removed from hass")
        self.hass.bus._async_remove_listener(f"{DOMAIN}_uptime_sensor_updated", self._handle_event)

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        _LOGGER.debug(f"Sensor {self.entity_id} added to hass")
        self.hass.bus.async_listen(f"{DOMAIN}_uptime_sensor_updated", self._handle_event)
        _LOGGER.debug(f"Sensor {self.entity_id} subscribed to event")





class PowerFlowSensor(SensorEntity):
    def __init__(self, sensor_info, hass, entry, dongle_id, bank_name):
        """Initialize the Power Flow sensor."""
        self.sensor_info = sensor_info
        self._name = sensor_info["name"]
        self._unique_id = f"{entry.entry_id}_{sensor_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = dongle_id.lower().replace("-", "_")
        self._device_id = dongle_id.lower().replace("-", "_")
        self._sensor_type = sensor_info["unique_id"]
        self.entity_id = f"sensor.{self._device_id}_{self._sensor_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._attribute1 = sensor_info.get("attribute1")
        self._attribute2 = sensor_info.get("attribute2")
        self._value1 = 0
        self._value2 = 0

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
        return self.sensor_info.get("unit_of_measurement")

    @property
    def device_class(self):
        return self.sensor_info.get("device_class")

    
    @property
    def extra_state_attributes(self):
        return {
            self._attribute1: self._value1,
            self._attribute2: self._value2,

        }

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

        if event_entity_id.endswith(self._attribute1.lower()):
            self._value1 = float(value)
        elif event_entity_id.endswith(self._attribute2.lower()):
            self._value2 = float(value)

        # Calculate the flow value
        if self._value1 > 0:
            self._state = -1 * self._value1
        else:
            self._state = self._value2

        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        self.hass.bus.async_listen(f"{DOMAIN}_sensor_updated", self._handle_event)
        _LOGGER.debug(f"Sensor {self.entity_id} subscribed to event")

    async def async_will_remove_from_hass(self):
        """Unsubscribe from events when removed."""
        _LOGGER.debug(f"Sensor {self.entity_id} will be removed from hass")
        self.hass.bus._async_remove_listener(f"{DOMAIN}_sensor_updated", self._handle_event)



class CombinedSensor(SensorEntity):
    def __init__(self, sensor_info, hass, entry, dongle_id):
        """Initialize the Combined sensor."""
        self.sensor_info = sensor_info
        self._name = sensor_info["name"]
        self._unique_id = f"{entry.entry_id}_{sensor_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = dongle_id.lower().replace("-", "_")
        self._device_id = dongle_id.lower().replace("-", "_")
        self._sensor_type = sensor_info["unique_id"]
        self.entity_id = f"sensor.{self._device_id}_{self._sensor_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._attributes = sensor_info.get("attributes", [])
        self._sensor_values = {attr: 0.0 for attr in self._attributes}  # Store individual sensor values

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
        return self.sensor_info.get("unit_of_measurement")

    @property
    def device_class(self):
        return self.sensor_info.get("device_class")


    @property
    def extra_state_attributes(self):
        return self._sensor_values

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

        if event_entity_id in self._sensor_values:
            self._sensor_values[event_entity_id] = float(value)

            # Example operation: Summing all sensor values
            self._state = sum(self._sensor_values.values())
            self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        """Unsubscribe from events when removed."""
        _LOGGER.debug(f"Sensor {self.entity_id} will be removed from hass")
        self.hass.bus._async_remove_listener(f"{DOMAIN}_sensor_updated", self._handle_event)

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        _LOGGER.debug(f"Sensor {self.entity_id} added to hass")
        self.hass.bus.async_listen(f"{DOMAIN}_sensor_updated", self._handle_event)
        _LOGGER.debug(f"Sensor {self.entity_id} subscribed to event")

class BankUpdateSensor(SensorEntity):
    def __init__(self, sensor_info, hass, entry, dongle_id, bank_name):
        """Initialize the Bank Update sensor."""
        self.sensor_info = sensor_info
        self._name = sensor_info["name"]
        self._unique_id = f"{entry.entry_id}_{sensor_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = dongle_id.lower().replace("-", "_")
        self._device_id = dongle_id.lower().replace("-", "_")
        self._sensor_type = sensor_info["unique_id"]
        self.entity_id = f"sensor.{self._device_id}_{self._sensor_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        
        # Initialize attributes with None values
        self._attributes = {attr: None for attr in sensor_info.get("attributes", [])}

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        """Return the most recent update time."""
        return self._state

    @property
    def device_class(self):
        return self.sensor_info.get("device_class")

    @property
    def extra_state_attributes(self):
        return self._attributes

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._dongle_id)},
            "name": f"Inverter {self._dongle_id}",
            "manufacturer": f"{self._manufacturer}",
        }

    @callback
    def _handle_bank_update(self, event):
        """Handle bank update events."""
        bank_name = event.data.get("bank_name")
        _LOGGER.debug(f"Update Event Called for: {bank_name}")
        if bank_name:
            current_time = datetime.now().isoformat()
            attr_name = f"{bank_name}_last_update"
            _LOGGER.debug(f"Updating Attribute name: {attr_name}")
            
            if attr_name in self._attributes:
                self._attributes[attr_name] = current_time
                self._state = current_time  # Update state to most recent update
                self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        """Unsubscribe from events when removed."""
        _LOGGER.debug(f"Unsubscribing from bank update event for {self.entity_id}")
        self.hass.bus._async_remove_listener(f"{DOMAIN}_bank_updated", self._handle_bank_update)

    async def async_added_to_hass(self):
        """Subscribe to events when added to hass."""
        _LOGGER.debug(f"Subscribing to bank update event for {self.entity_id}")
        self.hass.bus.async_listen(f"{DOMAIN}_bank_updated", self._handle_bank_update)


        