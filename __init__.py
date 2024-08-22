import asyncio
import json
import logging
from homeassistant.core import HomeAssistant, callback  # Import the callback decorator
from homeassistant.const import Platform
from .const import DOMAIN, ENTITIES, DEFAULT_MQTT_SERVER, DEFAULT_MQTT_PORT
from .mqtt import MQTTHandler

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry):
    """Set up the Monitor My Solar component from a config entry."""
    config = entry.data
    inverter_brand = config.get("inverter_brand")
    dongle_id = config.get("dongle_id")
    mqtt_server = config.get("mqtt_server", DEFAULT_MQTT_SERVER)
    mqtt_port = config.get("mqtt_port", DEFAULT_MQTT_PORT)
    mqtt_username = config.get("mqtt_username", "")
    mqtt_password = config.get("mqtt_password", "")

    _LOGGER.info("Setting up Monitor My Solar for %s", inverter_brand)

    brand_entities = ENTITIES.get(inverter_brand, {})
    if not brand_entities:
        _LOGGER.error("No entities defined for inverter brand: %s", inverter_brand)
        return False

    # Determine if using HA MQTT or Paho MQTT
    use_ha_mqtt = mqtt_server == DEFAULT_MQTT_SERVER

    # Initialize and set up the MQTT handler
    mqtt_handler = MQTTHandler(hass, use_ha_mqtt)
    await mqtt_handler.async_setup(entry)
    hass.data[DOMAIN] = {"mqtt_handler": mqtt_handler}
    client = mqtt_handler.client
    # Define MQTT event callbacks
    @callback
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            _LOGGER.info("Connected to MQTT server")
            for entity_type, banks in brand_entities.items():
                for bank_name in banks.keys():
                    topic = f"{dongle_id}/{bank_name}"
                    client.subscribe(topic)
                    _LOGGER.warning("Subscribed to topic: %s", topic)
            client.subscribe(f"{dongle_id}/firmwarecode/response")
            _LOGGER.warning("Subscribed to Firmware code topic: %s", f"{dongle_id}/firmwarecode/response")
            client.subscribe(f"{dongle_id}/update")
            client.subscribe(f"{dongle_id}/response")
            _LOGGER.info("Subscribed to firmwarecode, update, and response topics")

            firmware_code = config.get("firmware_code")
            if firmware_code:
                hass.data[DOMAIN]["firmware_code"] = firmware_code
                _LOGGER.info(f"Firmware code found in config entry: {firmware_code}")
                hass.async_create_task(
                    setup_entities(hass, entry, inverter_brand, dongle_id, firmware_code)
                )
            else:
                _LOGGER.warning("Requesting firmware code...")
                client.publish(f"{dongle_id}/firmwarecode/request", "")
        else:
            _LOGGER.error("Failed to connect to MQTT server, return code %d", rc)

    @callback
    async def on_message(msg):
        if msg.topic == f"{dongle_id}/firmwarecode/response":
            try:
                data = json.loads(msg.payload)
                firmware_code = data.get("FWCode")
                if firmware_code:
                    hass.data[DOMAIN]["firmware_code"] = firmware_code
                    _LOGGER.info(f"Firmware code received: {firmware_code}")

                    # Update the config entry without awaiting, since it's not a coroutine
                    hass.config_entries.async_update_entry(
                        entry, data={**entry.data, "firmware_code": firmware_code}
                    )

                    # Setup entities also scheduled directly in the event loop
                    await setup_entities(hass, entry, inverter_brand, dongle_id, firmware_code)
                else:
                    _LOGGER.error("No firmware code found in response")
            except json.JSONDecodeError:
                _LOGGER.error("Failed to decode JSON from response")
        else:
            await process_message(hass, msg.payload, dongle_id, inverter_brand)

    if use_ha_mqtt:
        await client.async_subscribe(hass, topic=f"{dongle_id}/#", msg_callback=on_message)


        
        # Now that we're subscribed, publish the firmware request
        firmware_code = config.get("firmware_code")
        if firmware_code:
            hass.data[DOMAIN]["firmware_code"] = firmware_code
            _LOGGER.info(f"Firmware code found in config entry: {firmware_code}")
            await setup_entities(hass, entry, inverter_brand, dongle_id, firmware_code)
        else:
            _LOGGER.warning("Requesting firmware code...")
            client.publish(hass, topic=f"{dongle_id}/firmwarecode/request", payload="")
    else:
        client.on_connect = on_connect
        client.on_message = on_message
        client.loop_start()

    # Wait for the firmware code response if it wasn't found in the config entry
    if "firmware_code" not in config:
        await asyncio.sleep(10)
        if "firmware_code" not in hass.data[DOMAIN]:
            _LOGGER.error("Firmware code response not received within timeout")
            return False

    return True

async def setup_entities(hass, entry, inverter_brand, dongle_id, firmware_code):
    """Set up the entities based on the firmware code."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, Platform.SENSOR)
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, Platform.SWITCH)
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, Platform.NUMBER)
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, Platform.TIME)
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, Platform.SELECT)
    )

def determine_entity_type(entity_id_suffix, inverter_brand):
    """Determine the entity type based on the entity_id_suffix."""
    brand_entities = ENTITIES.get(inverter_brand, {})
    if not brand_entities:
        _LOGGER.warning(f"No entities defined for inverter brand: {inverter_brand}. Defaulting to 'sensor'.")
        return "sensor"

    entity_id_suffix_lower = entity_id_suffix.lower()

    for entity_type in ["sensor", "switch", "number", "time", "time_hhmm"]:
        if entity_type in brand_entities:
            for bank_name, entities in brand_entities[entity_type].items():
                for entity in entities:
                    if entity["unique_id"].lower() == entity_id_suffix_lower:
                        if entity_type == "time_hhmm":
                            _LOGGER.debug(f"Matched entity_id_suffix '{entity_id_suffix_lower}' to entity type 'time'.")
                            return "time"
                        _LOGGER.debug(f"Matched entity_id_suffix '{entity_id_suffix_lower}' to entity type '{entity_type}'.")
                        return entity_type

    _LOGGER.warning(f"Could not match entity_id_suffix '{entity_id_suffix_lower}'. Defaulting to 'sensor'.")
    return "sensor"  # Default to sensor if no match is found


async def process_message(hass, payload, dongle_id, inverter_brand):
    """Process incoming MQTT message and update entity states."""
    try:
        data = json.loads(payload)
    except ValueError:
        _LOGGER.error("Invalid JSON payload received")
        return

    # Replace colons in dongle_id with underscores to match Home Assistant entity ID format
    formatted_dongle_id = dongle_id.replace(":", "_").lower()

    for entity_id_suffix, state in data.items():
        # Format entity_id_suffix by replacing colons with underscores
        formatted_entity_id_suffix = entity_id_suffix.lower().replace("-", "_").replace(":", "_")
        entity_type = determine_entity_type(formatted_entity_id_suffix, inverter_brand)
        entity_id = (
            f"{entity_type}.{formatted_dongle_id}_{formatted_entity_id_suffix}"
        )
        _LOGGER.debug(f"Firing event for entity {entity_id} with state {state}")
        hass.bus.async_fire(
            f"{DOMAIN}_{entity_type}_updated", {"entity": entity_id, "value": state}
        )
        _LOGGER.debug(f"Event fired for entity {entity_id} with state {state}")

