import asyncio
import json
import logging
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import Platform
from homeassistant.helpers.event import async_call_later
from homeassistant.components import mqtt
from .const import DOMAIN, ENTITIES, DEFAULT_MQTT_SERVER, DEFAULT_MQTT_PORT
from .mqttHandeler import MQTTHandler

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry):
    try:
        _LOGGER.info(f"Setting up Monitor My Solar for {entry.data.get('inverter_brand')}")

        config = entry.data
        inverter_brand = config.get("inverter_brand")
        dongle_id = config.get("dongle_id")
        mqtt_server = config.get("mqtt_server", DEFAULT_MQTT_SERVER)
        mqtt_port = config.get("mqtt_port", DEFAULT_MQTT_PORT)
        mqtt_username = config.get("mqtt_username", "")
        mqtt_password = config.get("mqtt_password", "")

        brand_entities = ENTITIES.get(inverter_brand, {})
        if not brand_entities:
            _LOGGER.error(f"No entities defined for inverter brand: {inverter_brand}")
            return False

        use_ha_mqtt = mqtt_server == DEFAULT_MQTT_SERVER

        mqtt_handler = MQTTHandler(hass, use_ha_mqtt)
        await mqtt_handler.async_setup(entry)
        hass.data[DOMAIN] = {"mqtt_handler": mqtt_handler}
        client = mqtt_handler.client

        firmware_code = config.get("firmware_code")
        if firmware_code:
            hass.data[DOMAIN]["firmware_code"] = firmware_code

        @callback
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                _LOGGER.info("Connected to MQTT server")
                try:
                    for entity_type, banks in brand_entities.items():
                        for bank_name in banks.keys():
                            topic = f"{dongle_id}/{bank_name}"
                            client.subscribe(topic)
                            _LOGGER.debug(f"Subscribed to topic: {topic}")
                    client.subscribe(f"{dongle_id}/firmwarecode/response")
                    client.subscribe(f"{dongle_id}/update")
                    client.subscribe(f"{dongle_id}/response")
                    client.subscribe(f"{dongle_id}/#")

                    if firmware_code:
                        hass.loop.call_soon_threadsafe(
                            hass.async_create_task, 
                            setup_entities(hass, entry, inverter_brand, dongle_id, firmware_code)
                        )
                    else:
                        _LOGGER.warning("Requesting firmware code...Paho MQTT")
                        client.publish(f"{dongle_id}/firmwarecode/request", "")
                except Exception as e:
                    _LOGGER.error(f"Error during MQTT connection setup: {e}")
            else:
                _LOGGER.error(f"Failed to connect to MQTT server, return code {rc}")

        def on_message(client, userdata, message):
            """Handle incoming MQTT messages."""
            try:
                topic = message.topic
                payload = message.payload.decode("utf-8")
                _LOGGER.debug(f"Received message on topic {topic}")
                
                hass.loop.call_soon_threadsafe(
                    hass.async_create_task, process_incoming_message(hass, topic, payload, entry, dongle_id, inverter_brand)
                )
            except Exception as e:
                _LOGGER.error(f"Error processing MQTT message: {e}")

        async def process_incoming_message(hass, topic, payload, entry, dongle_id, inverter_brand):
            if topic == f"{dongle_id}/firmwarecode/response":
                _LOGGER.debug("Received firmware code response")
                _LOGGER.debug(f"Payload: {payload}")
                try:
                    data = json.loads(payload)
                    firmware_code = data.get("FWCode")
                    if firmware_code:
                        hass.data[DOMAIN]["firmware_code"] = firmware_code
                        _LOGGER.debug(f"Firmware code received: {firmware_code}")

                        hass.config_entries.async_update_entry(
                            entry, data={**entry.data, "firmware_code": firmware_code}
                        )
                        await setup_entities(hass, entry, inverter_brand, dongle_id, firmware_code)
                    else:
                        _LOGGER.error("No firmware code found in response")
                except json.JSONDecodeError:
                    _LOGGER.error("Failed to decode JSON from response")
            else:
                await process_message(hass, payload, dongle_id, inverter_brand)

        if use_ha_mqtt:
            try:
                def create_mqtt_callback(entry, dongle_id, inverter_brand):
                    async def mqtt_callback(msg):
                        await process_incoming_message(hass, msg.topic, msg.payload, entry, dongle_id, inverter_brand)
                    return mqtt_callback

                callback_with_args = create_mqtt_callback(entry, dongle_id, inverter_brand)

                await mqtt.async_subscribe(hass, f"{dongle_id}/#", callback_with_args)

                if firmware_code:
                    await setup_entities(hass, entry, inverter_brand, dongle_id, firmware_code)
                else:
                    _LOGGER.debug("Requesting firmware code... HA MQTT")
                    await mqtt.async_publish(hass, f"{dongle_id}/firmwarecode/request", "")
            except Exception as e:
                _LOGGER.error(f"Error during HA MQTT setup: {e}")
                return False
        else:
            try:
                client.on_connect = on_connect
                client.on_message = on_message
                client.loop_start()
            except Exception as e:
                _LOGGER.error(f"Error during external MQTT setup: {e}")
                return False

        if "firmware_code" not in config:
            async def firmware_timeout(_):
                if "firmware_code" not in hass.data[DOMAIN]:
                    _LOGGER.error("Firmware code response not received within timeout")
                    await async_unload_entry(hass, entry)

            async_call_later(hass, 15, firmware_timeout)

        # Register the reload service
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

async def process_message(hass, payload, dongle_id, inverter_brand):
    """Process incoming MQTT message and update entity states."""
    try:
        data = json.loads(payload)
    except ValueError:
        _LOGGER.error("Invalid JSON payload received")
        return

    formatted_dongle_id = dongle_id.replace(":", "_").lower()

    for entity_id_suffix, state in data.items():
        formatted_entity_id_suffix = entity_id_suffix.lower().replace("-", "_").replace(":", "_")
        entity_type = determine_entity_type(formatted_entity_id_suffix, inverter_brand)
        entity_id = f"{entity_type}.{formatted_dongle_id}_{formatted_entity_id_suffix}"
        _LOGGER.debug(f"Firing event for entity {entity_id} with state {state}")
        hass.bus.async_fire(f"{DOMAIN}_{entity_type}_updated", {"entity": entity_id, "value": state})
        _LOGGER.debug(f"Event fired for entity {entity_id} with state {state}")
