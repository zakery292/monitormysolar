# config_flow.py
"""Config flow for Inverter MQTT."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import mqtt
from homeassistant.helpers import aiohttp_client

from .const import (
    DOMAIN,
    DEFAULT_MQTT_SERVER,
    DEFAULT_MQTT_PORT,
    DEFAULT_MQTT_USERNAME,
    DEFAULT_MQTT_PASSWORD,
    SENSORS,
)

_LOGGER = logging.getLogger(__name__)

class InverterMQTTFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Inverter MQTT."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            valid = await self._test_mqtt_connection(
                user_input.get("mqtt_server", DEFAULT_MQTT_SERVER),
                user_input.get("mqtt_port", DEFAULT_MQTT_PORT),
                user_input.get("mqtt_username", ""),
                user_input.get("mqtt_password", ""),
            )
            if valid:
                return self.async_create_entry(title="Inverter MQTT Configuration", data=user_input)
            else:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("inverter_brand", default="Solis"): vol.In(["Solis", "Lux", "Solax", "Growatt"]),
                    vol.Optional("mqtt_server", default=DEFAULT_MQTT_SERVER): str,
                    vol.Optional("mqtt_port", default=DEFAULT_MQTT_PORT): int,
                    vol.Optional("mqtt_username", default=""): str,
                    vol.Optional("mqtt_password", default=""): str,
                    vol.Required("dongle_id"): str,
                }
            ),
            errors=errors,
        )

    async def _test_mqtt_connection(self, server, port, username, password):
        """Test if we can connect to the MQTT broker."""
        try:
            # Use the Home Assistant MQTT integration to test the connection
            await mqtt.async_publish(self.hass, "test/topic", "test message", qos=0)
            return True
        except Exception as e:
            _LOGGER.error(f"Failed to connect to MQTT broker: {e}")
            return False

    async def async_setup_sensors(self, config):
        inverter_brand = config["inverter_brand"]
        sensors = SENSORS.get(inverter_brand, [])

        for sensor in sensors:
            if sensor["type"] == "sensor":
                await self.hass.config_entries.async_forward_entry_setup(config, "sensor")
            elif sensor["type"] == "switch":
                await self.hass.config_entries.async_forward_entry_setup(config, "switch")
            elif sensor["type"] == "number":
                await self.hass.config_entries.async_forward_entry_setup(config, "number")
            elif sensor["type"] == "time":
                await self.hass.config_entries.async_forward_entry_setup(config, "time")
