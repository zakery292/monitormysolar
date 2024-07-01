# config_flow.py
"""Config flow for Inverter MQTT."""
import logging
import voluptuous as vol
from homeassistant import config_entries, core
from .const import (
    DOMAIN, 
    DEFAULT_MQTT_SERVER, 
    DEFAULT_MQTT_PORT, 
    DEFAULT_MQTT_USERNAME, 
    DEFAULT_MQTT_PASSWORD, 
    SENSORS
)
import json
import os
import aiohttp

_LOGGER = logging.getLogger(__name__)

LANGUAGES_FOLDER = os.path.join(os.path.dirname(__file__), "translations")

def load_translations(lang):
    path = os.path.join(LANGUAGES_FOLDER, f"{lang}.json")
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

class InverterMQTTFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Inverter MQTT."""
    async def async_step_user(self, user_input=None):
        translations = load_translations(self.hass.config.language)
        if user_input is not None:
            await self.async_setup_sensors(user_input)
            return self.async_create_entry(title=translations["title"], data=user_input)
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("inverter_brand", default="Solis"): vol.In(["Solis", "Lux", "Solax", "Growatt"]),
                    vol.Optional("mqtt_server", default=DEFAULT_MQTT_SERVER): str,
                    vol.Optional("mqtt_port", default=DEFAULT_MQTT_PORT): int,
                    vol.Optional("mqtt_username", default=DEFAULT_MQTT_USERNAME): str,
                    vol.Optional("mqtt_password", default=DEFAULT_MQTT_PASSWORD): str,
                    vol.Required("dongle_id"): str,
                }
            ),
        )

    async def async_setup_sensors(self, config):
        inverter_brand = config["inverter_brand"]
        sensors = SENSORS.get(inverter_brand, [])

        for sensor in sensors:
            if sensor["type"] == "sensor":
                await self.hass.config_entries.async_forward_entry_setup(self, "sensor")
            elif sensor["type"] == "switch":
                await self.hass.config_entries.async_forward_entry_setup(self, "switch")
            elif sensor["type"] == "number":
                await self.hass.config_entries.async_forward_entry_setup(self, "number")
            elif sensor["type"] == "time":
                await self.hass.config_entries.async_forward_entry_setup(self, "time")
