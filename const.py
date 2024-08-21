"""Constants for Inverter MQTT."""
from logging import Logger, getLogger

Logger: Logger = getLogger(__package__)

# Domain for the integration
DOMAIN = "inverter_mqtt"

# Default MQTT configuration for Home Assistant broker
DEFAULT_MQTT_SERVER = "mqtt://core-mosquitto"
DEFAULT_MQTT_PORT = 1883
DEFAULT_MQTT_USERNAME = ""
DEFAULT_MQTT_PASSWORD = ""

# Sensor definitions
SENSORS = {
    "Solis": [
        {"name": "Voltage", "type": "sensor", "unique_id": "voltage", "state_class": "measurement", "unit": "V"},
        {"name": "Current", "type": "sensor", "unique_id": "current", "state_class": "measurement", "unit": "A"},
        {"name": "Power", "type": "sensor", "unique_id": "power", "state_class": "measurement", "unit": "W"},
        {"name": "Output Power", "type": "sensor", "unique_id": "output_power", "state_class": "measurement", "unit": "W"},
        {"name": "AC Charge Start1", "type": "time", "unique_id": "ac_charge_start1"},
        {"name": "AC Charge End1", "type": "time", "unique_id": "ac_charge_end1"},
        {"name": "Inverter Status", "type": "switch", "unique_id": "inverter_status"},
        {"name": "Setpoint", "type": "number", "unique_id": "setpoint", "unit": "°C"},
    ],
    "Lux": [
        {"name": "Energy", "type": "sensor", "unique_id": "energy", "state_class": "measurement", "unit": "kWh"},
        {"name": "Temperature", "type": "sensor", "unique_id": "temperature", "state_class": "measurement", "unit": "°C"},
        {"name": "Setpoint", "type": "number", "unique_id": "setpoint", "unit": "°C"},
    ],
    "Solax": [
        {"name": "Battery Level", "type": "sensor", "unique_id": "battery_level", "state_class": "measurement", "unit": "%"},
        {"name": "Inverter Status", "type": "switch", "unique_id": "inverter_status"},
    ],
    "Growatt": [
        {"name": "Output Power", "type": "sensor", "unique_id": "output_power", "state_class": "measurement", "unit": "W"},
        {"name": "AC Charge Start1", "type": "time", "unique_id": "ac_charge_start1"},
        {"name": "AC Charge End1", "type": "time", "unique_id": "ac_charge_end1"},
    ],
}
