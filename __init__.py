# __init__.py
import logging
import json
from homeassistant.core import HomeAssistant
from homeassistant.components.mqtt import async_subscribe
from .const import DOMAIN, SENSORS

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Inverter MQTT component."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry):
    """Set up Inverter MQTT from a config entry."""
    mqtt_server = entry.data.get("mqtt_server")
    mqtt_port = entry.data.get("mqtt_port")
    mqtt_username = entry.data.get("mqtt_username")
    mqtt_password = entry.data.get("mqtt_password")
    dongle_id = entry.data.get("dongle_id")

    # Subscribe to the necessary topics
    async def message_received(message):
        """Handle new MQTT messages."""
        try:
            payload = json.loads(message.payload)
            _LOGGER.warning(f'Message received on topic {message.topic}: {payload}')
        except json.JSONDecodeError as e:
            _LOGGER.error(f"Failed to decode JSON payload: {e}")
            _LOGGER.error(f"Message payload: {message.payload}")
            return

        if 'dongle' in payload and 'hold' in payload['dongle']:
            await handle_hold_payload(hass, dongle_id, payload['dongle']['hold'])
        else:
            _LOGGER.warning("No 'hold' key found in payload")

        if 'dongle' in payload and 'input' in payload['dongle']:
            await handle_input_payload(hass, dongle_id, payload['dongle']['input'])
        else:
            _LOGGER.warning("No 'input' key found in payload")

    async def handle_hold_payload(hass: HomeAssistant, dongle_id, hold_payload):
        """Handle the 'hold' payload."""
        for entity, value in hold_payload.items():
            if entity.startswith('switch'):
                event_type = f"{DOMAIN}_switch_updated"
            elif entity.startswith('AC_Charge_Start1') or entity.startswith('AC_Charge_End1'):
                base_entity = entity.rsplit('_', 1)[0]
                event_type = f"{DOMAIN}_time_updated"
                hh_key = f"{base_entity}_HH"
                mm_key = f"{base_entity}_MM"
                _LOGGER.warning(f'Updating time entity {base_entity} with HH: {hh_key}, MM: {mm_key}')
                if hh_key in hold_payload and mm_key in hold_payload:
                    hh = hold_payload[hh_key]
                    mm = hold_payload[mm_key]
                    hass.bus.fire(event_type, {
                        "entity": base_entity,
                        "hh": hh,
                        "mm": mm
                    })
                    _LOGGER.warning(f'Fired event to set time entity {base_entity} to {hh:02}:{mm:02}')
                else:
                    _LOGGER.warning(f'Missing HH or MM keys for {entity}')
                continue
            else:
                event_type = f"{DOMAIN}_sensor_updated"

            _LOGGER.warning(f'Firing event to update state for {entity} to {value}')
            hass.bus.fire(event_type, {
                "entity": entity,
                "value": value
            })

    async def handle_input_payload(hass: HomeAssistant, dongle_id, input_payload):
        """Handle the 'input' payload."""
        _LOGGER.warning(f'Handling input payload: {input_payload}')
        for entity, value in input_payload.items():
            event_type = f"{DOMAIN}_sensor_updated"
            _LOGGER.warning(f'Firing event to update state for {entity} to {value}')
            hass.bus.fire(event_type, {
                "entity": entity,
                "value": value
            })

    await async_subscribe(hass, f"{dongle_id}/input", message_received)
    _LOGGER.info(f"Subscribed to {dongle_id}/input")
    await async_subscribe(hass, f"{dongle_id}/hold", message_received)
    _LOGGER.info(f"Subscribed to {dongle_id}/hold")

    # Forward the setup to the platform
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "switch")
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "number")
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "time")
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    await hass.config_entries.async_forward_entry_unload(entry, "switch")
    await hass.config_entries.async_forward_entry_unload(entry, "number")
    await hass.config_entries.async_forward_entry_unload(entry, "time")
    return True
