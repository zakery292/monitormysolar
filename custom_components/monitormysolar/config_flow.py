import logging
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class InverterMQTTFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Inverter MQTT."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        _LOGGER.debug("Loading the user step form")

        if user_input is not None:
            _LOGGER.debug("User input received: %s", user_input)

            # Once the user submits the form, create the entry
            return self.async_create_entry(
                title=f"{user_input['inverter_brand']} - {user_input['dongle_id']}",
                data=user_input,
            )

        _LOGGER.debug("Displaying the form with translations")

        schema = vol.Schema(
            {
                vol.Required("inverter_brand", default="Solis"): vol.In(
                    ["Solis", "Lux", "Solax", "Growatt"]
                ),
                vol.Required("dongle_id"): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_setup_entry(self, hass, entry):
        _LOGGER.info("Monitor My Solar Being Setup")
        return True
