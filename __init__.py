# __init__.py
import logging
import json
from homeassistant.helpers import discovery
from homeassistant.components.mqtt import async_subscribe, async_publish
from .const import DOMAIN, SENSORS

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    """Set up the Inverter MQTT component."""
    return True

async def async_setup_entry(hass, entry):
    """Set up Inverter MQTT from a config entry."""
    mqtt_server = entry.data.get("mqtt_server")
    mqtt_port = entry.data.get("mqtt_port")
    mqtt_username = entry.data.get("mqtt_username")
    mqtt_password = entry.data.get("mqtt_password")
    dongle_id = entry.data.get("dongle_id")

    # Subscribe to the necessary topics
    async def message_received(message):
        """Handle new MQTT messages."""
        payload = json.loads(message.payload)
        if 'hold' in payload:
            for entity, value in payload['hold'].items():
                entity_id = f"{dongle_id}_{entity}"
                hass.states.async_set(entity_id, value)
                if entity.startswith('switch'):
                    await hass.services.async_call(
                        'switch', 'turn_' + ('on' if value == 'on' else 'off'), {
                            'entity_id': entity_id
                        }
                    )
                elif entity.startswith(('AC_Charge_Start1', 'AC_Charge_End1')):
                    hh_key = f"{entity}_HH"
                    mm_key = f"{entity}_MM"
                    if hh_key in payload['hold'] and mm_key in payload['hold']:
                        hh = payload['hold'][hh_key]
                        mm = payload['hold'][mm_key]
                        time_entity_id = f"{dongle_id}_{entity}"
                        await hass.states.async_set(time_entity_id, f"{hh:02}:{mm:02}")

    await async_subscribe(hass, f"{dongle_id}/input", message_received)
    await async_subscribe(hass, f"{dongle_id}/hold", message_received)

    # Forward the setup to the platform
    hass.async_create_task(
        discovery.async_load_platform(
            hass, "sensor", DOMAIN, {}, entry
        )
    )
    hass.async_create_task(
        discovery.async_load_platform(
            hass, "switch", DOMAIN, {}, entry
        )
    )
    hass.async_create_task(
        discovery.async_load_platform(
            hass, "number", DOMAIN, {}, entry
        )
    )
    hass.async_create_task(
        discovery.async_load_platform(
            hass, "time", DOMAIN, {}, entry
        )
    )

    return True

async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    await hass.config_entries.async_forward_entry_unload(entry, "switch")
    await hass.config_entries.async_forward_entry_unload(entry, "number")
    await hass.config_entries.async_forward_entry_unload(entry, "time")
    return True
