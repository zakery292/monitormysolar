import asyncio
import json
import logging
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.helpers.event import async_call_later
from homeassistant.components import mqtt
from .const import DOMAIN, ENTITIES
from .mqttHandeler import MQTTHandler
from .coordinator import MonitorMySolar

_LOGGER = logging.getLogger(__name__)

type MonitorMySolarEntry = ConfigEntry[MonitorMySolar]

async def async_setup_entry(hass: HomeAssistant, entry: MonitorMySolarEntry):
    try:
        _LOGGER.info(f"Setting up Monitor My Solar for {entry.data.get('inverter_brand')}")

        coordinator = MonitorMySolar(hass, entry)

        config = entry.data
        inverter_brand = config.get("inverter_brand")
        dongle_id = config.get("dongle_id")
        firmware_code = config.get("firmware_code")

        # Initialize the MQTT handler and store it in the hass data under the domain
        mqtt_handler = MQTTHandler(hass)
        # hass.data.setdefault(DOMAIN, {})["mqtt_handler"] = mqtt_handler

        entry.runtime_data = coordinator

        brand_entities = ENTITIES.get(inverter_brand, {})
        if not brand_entities:
            _LOGGER.error(f"No entities defined for inverter brand: {inverter_brand}")
            return False

        async def process_incoming_message(msg):
            if msg.topic == f"{dongle_id}/firmwarecode/response":
                _LOGGER.debug("Received firmware code response")
                try:
                    data = json.loads(msg.payload)
                    firmware_code = data.get("FWCode")
                    if firmware_code:
                        coordinator.firmware_code = firmware_code
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
                await process_message(hass, entry, msg.topic, msg.payload, dongle_id, inverter_brand)


        await mqtt.async_subscribe(hass, f"{dongle_id}/#", process_incoming_message)

        if not firmware_code:
            _LOGGER.debug("Requesting firmware code...")
            await mqtt.async_publish(hass, f"{dongle_id}/firmwarecode/request", "")

            async def firmware_timeout(_):
                if "" == coordinator.firmware_code:
                    _LOGGER.error("Firmware code response not received within timeout")
                    await async_unload_entry(hass, entry)

            async_call_later(hass, 15, firmware_timeout)
        else:
            coordinator.firmware_code = firmware_code
            setup_success = await setup_entities(hass, entry, inverter_brand, dongle_id, firmware_code)
            if not setup_success:
                return False

        async def reload_service_call(service_call):
            try:
                _LOGGER.info("Reloading Monitor My Solar integration")
                await async_unload_entry(hass, entry)
                firmware_code = coordinator.firmware_code
                await async_setup_entry(hass, entry)
            except Exception as e:
                _LOGGER.error(f"Error during reload: {e}")

        hass.services.async_register(DOMAIN, "reload", reload_service_call)

        _LOGGER.info("Monitor My Solar setup completed successfully")
        return True
    except Exception as e:
        _LOGGER.error(f"Failed to set up Monitor My Solar: {e}")
        return False

async def async_unload_entry(hass, entry: MonitorMySolarEntry):
    """Unload a config entry."""
    _LOGGER.info(f"Unloading Monitor My Solar for {entry.data.get('inverter_brand')}")
    try:
        unload_ok = await hass.config_entries.async_unload_platforms(entry, [
            Platform.SENSOR,
            Platform.BINARY_SENSOR,
            Platform.SWITCH,
            Platform.NUMBER,
            Platform.TIME,
            Platform.SELECT,
            Platform.BUTTON,
            Platform.UPDATE,
        ])
        if unload_ok:
            hass.data.pop(DOMAIN)
        return unload_ok
    except Exception as e:
        _LOGGER.error(f"Error during unload: {e}")
        return False

async def setup_entities(hass, entry: MonitorMySolarEntry, inverter_brand, dongle_id, firmware_code):
    """Set up the entities based on the firmware code."""
    platforms = [
        Platform.SENSOR,
        Platform.BINARY_SENSOR,
        Platform.SWITCH,
        Platform.NUMBER,
        Platform.TIME,
        Platform.SELECT,
        Platform.BUTTON,
        Platform.UPDATE,
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

async def process_message(hass, entry: MonitorMySolarEntry, topic, payload, dongle_id, inverter_brand):
    """Process incoming MQTT message and update entity states."""
    try:
        data = json.loads(payload)
        bank_name = topic.split('/')[-1]  # Gets 'inputbank1', 'holdbank2', etc.
        hass.bus.async_fire(f"{DOMAIN}_bank_updated", {"bank_name": bank_name})
        _LOGGER.debug(f"Event fired for bank {bank_name}")
        coordinator = entry.runtime_data
        
    except ValueError:
        _LOGGER.error("Invalid JSON payload received")
        return

    # Handle new payload structure while maintaining backward compatibility
    serial_number = None
    payload_data = {}
    events_data = {}
    fault_data = {}
    warning_data = {}

    if isinstance(data, dict):
        if "Serialnumber" in data:
            serial_number = data.get("Serialnumber")
            
        if "payload" in data:
            # New format with data wrapper
            payload_data = data["payload"]
            events_data = data.get("events", {})
            # Get fault and warning data from events object
            fault_data = events_data.get("fault", {})
            warning_data = events_data.get("warning", {})
            # **Add this block to extract and store versions**
        else:
            # Old format - direct key-value pairs
            payload_data = data
    if "SW_VERSION" in payload_data:
        fw_version = payload_data["SW_VERSION"]
        coordinator.current_fw_version = fw_version
        _LOGGER.debug(f"Current firmware version set: {fw_version}")
        # Fire event for update entity
        entity_id = f"update.{dongle_id}_firmware_update"
        hass.bus.async_fire(f"{DOMAIN}_update_version", {
            "entity": entity_id,
            "value": fw_version
        })

    # Update UI version
    if "UI_VERSION" in payload_data:
        ui_version = payload_data["UI_VERSION"]
        coordinator.current_ui_version = ui_version
        _LOGGER.debug(f"Current UI version set: {ui_version}")
        # Fire event for update entity
        entity_id = f"update.{dongle_id}_ui_update"
        hass.bus.async_fire(f"{DOMAIN}_update_version", {
            "entity": entity_id,
            "value": ui_version
        })



    formatted_dongle_id = dongle_id.replace(":", "_").lower()

    # Process fault data
    if fault_data:
        _LOGGER.debug(f"Processing fault data: {fault_data}")
        fault_value = fault_data.get("value", 0)
        entity_id = f"sensor.{formatted_dongle_id}_fault_status"
        
        if fault_value == 0:
            hass.bus.async_fire(f"{DOMAIN}_fault_updated", {
                "entity": entity_id,
                "value": {
                    "value": 0,
                    "description": None  # This will trigger "No Fault" state
                }
            })
        else:
            descriptions = fault_data.get("descriptions", ["Unknown Fault"])
            timestamp = fault_data.get("timestamp", "Unknown")
            hass.bus.async_fire(f"{DOMAIN}_fault_updated", {
                "entity": entity_id,
                "value": {
                    "value": fault_value,
                    "description": ", ".join(descriptions),
                    "start_time": timestamp,
                    "end_time": "Ongoing"
                }
            })

    # Process warning data
    if warning_data:
        _LOGGER.debug(f"Processing warning data: {warning_data}")
        warning_value = warning_data.get("value", 0)
        entity_id = f"sensor.{formatted_dongle_id}_warning_status"
        
        if warning_value == 0:
            hass.bus.async_fire(f"{DOMAIN}_warning_updated", {
                "entity": entity_id,
                "value": {
                    "value": 0,
                    "description": None  # This will trigger "No Warning" state
                }
            })
        else:
            descriptions = warning_data.get("descriptions", ["Unknown Warning"])
            timestamp = warning_data.get("timestamp", "Unknown")
            hass.bus.async_fire(f"{DOMAIN}_warning_updated", {
                "entity": entity_id,
                "value": {
                    "value": warning_value,
                    "description": ", ".join(descriptions),
                    "start_time": timestamp,
                    "end_time": "Ongoing"
                }
            })
    # Process main sensor data
    for entity_id_suffix, state in payload_data.items():
    # Skip if we've already handled version keys
        formatted_entity_id_suffix = entity_id_suffix.lower().replace("-", "_").replace(":", "_")
        entity_type = determine_entity_type(formatted_entity_id_suffix, inverter_brand)
        entity_id = f"{entity_type}.{formatted_dongle_id}_{formatted_entity_id_suffix}"
        _LOGGER.debug(f"Firing event for entity {entity_id} with state {state}")
        hass.bus.async_fire(f"{DOMAIN}_{entity_type}_updated", {"entity": entity_id, "value": state})
        _LOGGER.debug(f"Event fired for entity {entity_id} with state {state}")

    # Process events data if present (new format)
    if events_data:
        _LOGGER.debug(f"Processing events data: {events_data}")
        # Fire events for state updates
        for event_id, event_state in events_data.items():
            formatted_event_id = event_id.lower().replace("-", "_").replace(":", "_")
            entity_id = f"binary_sensor.{formatted_dongle_id}_{formatted_event_id}"
            hass.bus.async_fire(f"{DOMAIN}_binary_sensor_updated", {
                "entity": entity_id, 
                "value": event_state
            })





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
