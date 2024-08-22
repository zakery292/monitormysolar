import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant
import asyncio
from .const import (
    DOMAIN,
    DEFAULT_MQTT_SERVER,
    DEFAULT_MQTT_PORT,
    DEFAULT_MQTT_USERNAME,
    DEFAULT_MQTT_PASSWORD,
)

_LOGGER = logging.getLogger(__name__)


class InverterMQTTFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Inverter MQTT."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        _LOGGER.warning("Loading the user step form")

        if user_input is not None:
            _LOGGER.warning("User input received: %s", user_input)

            mqtt_server = user_input.get("mqtt_server", DEFAULT_MQTT_SERVER)
            mqtt_port = user_input.get("mqtt_port", DEFAULT_MQTT_PORT)
            mqtt_username = user_input.get("mqtt_username", "")
            mqtt_password = user_input.get("mqtt_password", "")

            # Validate MQTT connection
            valid = await self._test_mqtt_connection(
                mqtt_server, mqtt_port, mqtt_username, mqtt_password
            )

            if valid:
                return self.async_create_entry(
                    title="Monitor My Solar",
                    data=user_input,
                )
            else:
                errors["base"] = "cannot_connect"

        _LOGGER.warning("Displaying the form with translations")

        schema = vol.Schema(
            {
                vol.Required("inverter_brand", default="Solis"): vol.In(
                    ["Solis", "Lux", "Solax", "Growatt"]
                ),
                vol.Optional("mqtt_server", default=DEFAULT_MQTT_SERVER): str,
                vol.Optional("mqtt_port", default=DEFAULT_MQTT_PORT): int,
                vol.Optional("mqtt_username", default=""): str,
                vol.Optional("mqtt_password", default=""): str,
                vol.Required("dongle_id"): str,
            }
        )

        form = self.async_show_form(step_id="user", data_schema=schema, errors=errors)

        _LOGGER.warning("Form: %s", form)
        return form

    async def _test_mqtt_connection(self, server, port, username, password):
        """Test the MQTT connection."""
        import paho.mqtt.client as mqtt_client

        client = mqtt_client.Client()

        if username:
            client.username_pw_set(username, password)

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                client.connected_flag = True
            else:
                client.connected_flag = False

        client.on_connect = on_connect
        client.connected_flag = False

        try:
            client.connect(server, port, 60)
            client.loop_start()
            for i in range(10):
                if client.connected_flag:
                    client.loop_stop()
                    return True
                await asyncio.sleep(1)
            client.loop_stop()
            return False
        except Exception as e:
            _LOGGER.error("MQTT connection failed: %s", e)
            return False

    async def async_setup_entry(self, hass, entry):
        _LOGGER.info("Monitor My Solar Being Setup")
        return True
