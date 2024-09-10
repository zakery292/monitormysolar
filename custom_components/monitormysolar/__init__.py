import asyncio
import json
import logging
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.helpers.event import async_call_later
from homeassistant.components import mqtt
from .const import DOMAIN, ENTITIES
from .mqttHandeler import MQTTHandler

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry):
    try:
        _LOGGER.info(f"Setting up Monitor My Solar for {entry.data.get('inverter_brand')}")

        config = entry.data
        inverter_brand = config.get("inverter_brand")
        dongle_id = config.get("dongle_id")
        firmware_code = config.get("firmware_code")

        # Initialize the MQTT handler and store it in the hass data under the domain
        mqtt_handler = MQTTHandler(hass)
        hass.data.setdefault(DOMAIN, {})["mqtt_handler"] = mqtt_handler

        brand_entities = ENTITIES.get(inverter_brand, {})
        if not brand_entities:
            _LOGGER.error(f"No entities defined for inverter brand: {inverter_brand}")
            return False

        # Initialize the DOMAIN key in hass.data if it doesn't exist
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}

        async def process_incoming_message(msg):
            if msg.topic == f"{dongle_id}/firmwarecode/response":
                _LOGGER.debug("Received firmware code response")
                try:
                    data = json.loads(msg.payload)
                    firmware_code = data.get("FWCode")
                    if firmware_code:
                        hass.data[DOMAIN]["firmware_code"] = firmware_code
                        _LOGGER.debug(f"Firmware code received: {firmware_code}")
                        hass.config_entries.async_update_entry(
                            entry, data={**entry.data, "firmware_code": firmware_code}
                        )
                        setup_success = await setup_entities(hass, entry, inverter_brand, dongle_id, firmware_code)
                        if not setup_success:
                            return False
                    else:
                        _LOGGER.error("No firmware code found in response")
                except json.JSONDecodeError:
                    _LOGGER.error("Failed to decode JSON from response")
            elif msg.topic == f"{dongle_id}/response":
                await mqtt_handler.response_received(msg)
            elif msg.topic == f"{dongle_id}/status":
                await process_status_message(hass, msg.payload, dongle_id)
            else:
                await process_message(hass, msg.payload, dongle_id, inverter_brand)

        await mqtt.async_subscribe(hass, f"{dongle_id}/#", process_incoming_message)

        if not firmware_code:
            _LOGGER.debug("Requesting firmware code...")
            await mqtt.async_publish(hass, f"{dongle_id}/firmwarecode/request", "")

            async def firmware_timeout(_):
                if "firmware_code" not in hass.data[DOMAIN]:
                    _LOGGER.error("Firmware code response not received within timeout")
                    await async_unload_entry(hass, entry)

            async_call_later(hass, 15, firmware_timeout)
        else:
            hass.data[DOMAIN]["firmware_code"] = firmware_code
            setup_success = await setup_entities(hass, entry, inverter_brand, dongle_id, firmware_code)
            if not setup_success:
                return False

        async def reload_service_call(service_call):
            try:
                _LOGGER.info("Reloading Monitor My Solar integration")
                await async_unload_entry(hass, entry)
                firmware_code = hass.data[DOMAIN].get("firmware_code")
                await async_setup_entry(hass, entry)
            except Exception as e:
                _LOGGER.error(f"Error during reload: {e}")

        hass.services.async_register(DOMAIN, "reload", reload_service_call)

        _LOGGER.info("Monitor My Solar setup completed successfully")
        return True
    except Exception as e:
        _LOGGER.error(f"Failed to set up Monitor My Solar: {e}")
        return False

async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    _LOGGER.info(f"Unloading Monitor My Solar for {entry.data.get('inverter_brand')}")
    try:
        unload_ok = await hass.config_entries.async_unload_platforms(entry, [
            Platform.SENSOR,
            Platform.SWITCH,
            Platform.NUMBER,
            Platform.TIME,
            Platform.SELECT,
            Platform.BUTTON,
        ])
        if unload_ok:
            hass.data.pop(DOMAIN)
        return unload_ok
    except Exception as e:
        _LOGGER.error(f"Error during unload: {e}")
        return False

async def setup_entities(hass, entry, inverter_brand, dongle_id, firmware_code):
    """Set up the entities based on the firmware code."""
    platforms = [
        Platform.SENSOR,
        Platform.SWITCH,
        Platform.NUMBER,
        Platform.TIME,
        Platform.SELECT,
        Platform.BUTTON,
    ]

    for platform in platforms:
        try:
            _LOGGER.info(f"Setting up {platform} entities for {inverter_brand}")
            if not hass.data.get(f"{DOMAIN}_setup_done_{platform}", False):
                await hass.config_entries.async_forward_entry_setups(entry, [platform])
                hass.data[f"{DOMAIN}_setup_done_{platform}"] = True
            _LOGGER.info(f"Successfully set up {platform} entities for {inverter_brand}")
        except Exception as e:
            _LOGGER.error(f"Error setting up {platform} entities: {e}")
            return False  # Return False if there's an error in setting up a platform
    return True  # Return True if all platforms are set up successfully


async def process_status_message(hass, payload, dongle_id):
    """Process incoming status MQTT message and update the status sensor."""
    try:
        data = json.loads(payload)
    except ValueError:
        _LOGGER.error("Invalid JSON payload received for status message")
        return

    # Check if the message follows the new structure with 'Serialnumber' and 'payload'
    if "Serialnumber" in data and "payload" in data:
        serial_number = data["Serialnumber"]
        status_data = data["payload"]
    else:
        serial_number = None  # For backward compatibility
        status_data = data  # Old format

    formatted_dongle_id = dongle_id.replace(":", "_").lower()
    entity_id = f"sensor.{formatted_dongle_id}_uptime"
    _LOGGER.debug(f"Firing event for status sensor {entity_id} with payload {status_data}")
    hass.bus.async_fire(f"{DOMAIN}_uptime_sensor_updated", {"entity": entity_id, "value": status_data})
    _LOGGER.debug(f"Event fired for status sensor {entity_id}")

async def process_message(hass, payload, dongle_id, inverter_brand):
    """Process incoming MQTT message and update entity states."""
    try:
        data = json.loads(payload)
    except ValueError:
        _LOGGER.error("Invalid JSON payload received")
        return

    # Check if the message follows the new structure with 'Serialnumber' and 'payload'
    if "Serialnumber" in data and "payload" in data:
        serial_number = data["Serialnumber"]
        payload_data = data["payload"]
    else:
        serial_number = None  # For backward compatibility, handle without serial number
        payload_data = data  # Old format

    formatted_dongle_id = dongle_id.replace(":", "_").lower()

    for entity_id_suffix, state in payload_data.items():
        formatted_entity_id_suffix = entity_id_suffix.lower().replace("-", "_").replace(":", "_")
        entity_type = determine_entity_type(formatted_entity_id_suffix, inverter_brand)
        entity_id = f"{entity_type}.{formatted_dongle_id}_{formatted_entity_id_suffix}"
        _LOGGER.debug(f"Firing event for entity {entity_id} with state {state}")
        hass.bus.async_fire(f"{DOMAIN}_{entity_type}_updated", {"entity": entity_id, "value": state})
        _LOGGER.debug(f"Event fired for entity {entity_id} with state {state}")


def determine_entity_type(entity_id_suffix, inverter_brand):
    """Determine the entity type based on the entity_id_suffix."""
    brand_entities = ENTITIES.get(inverter_brand, {})
    if not brand_entities:
        _LOGGER.debug(f"No entities defined for inverter brand: {inverter_brand}. Defaulting to 'sensor'.")
        return "sensor"

    entity_id_suffix_lower = entity_id_suffix.lower()
    _LOGGER.debug(f"Looking for entity_id_suffix '{entity_id_suffix_lower}' in brand '{inverter_brand}'.")

    for entity_type in ["sensor", "switch", "number", "time", "time_hhmm", "button", "select"]:
        if entity_type in brand_entities:
            for bank_name, entities in brand_entities[entity_type].items():
                _LOGGER.debug(f"Checking in bank '{bank_name}' for entity_type '{entity_type}'.")
                for entity in entities:
                    unique_id_lower = entity["unique_id"].lower()
                    _LOGGER.debug(f"Comparing with unique_id '{unique_id_lower}' for entity_type '{entity_type}'.")
                    if unique_id_lower == entity_id_suffix_lower:
                        if entity_type == "time_hhmm":
                            _LOGGER.debug(f"Matched entity_id_suffix '{entity_id_suffix_lower}' to entity type 'time'.")
                            return "time"
                        _LOGGER.debug(f"Matched entity_id_suffix '{entity_id_suffix_lower}' to entity type '{entity_type}'.")
                        return entity_type

    _LOGGER.debug(f"Could not match entity_id_suffix '{entity_id_suffix_lower}'. Defaulting to 'sensor'.")
    return "sensor"
