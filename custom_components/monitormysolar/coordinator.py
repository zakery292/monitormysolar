from __future__ import annotations
import json
from typing import Any, cast
from propcache import cached_property

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    HomeAssistant,
    callback,
)
from homeassistant.helpers.event import (
    async_call_later,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .mqttHandeler import MQTTHandler

from .const import (
    DOMAIN,
    ENTITIES,
    LOGGER,
    PLATFORMS,
)

class MonitorMySolar(DataUpdateCoordinator[None]):

    def __init__(
            self,
            hass: HomeAssistant,
            entry: MonitorMySolarEntry,
        ) -> None:

        """Initialize the Coordinator."""
        self.hass = hass
        self.entry = entry
        self.mqtt_handler = {}
        self._firmware_code: str = entry.data.get("firmware_code", None)
        self.current_fw_version: str = ""
        self.current_ui_version: str = ""
        self.server_versions = {}
        self.entities = {}
        self._dongle_id: str = cast(str, self.entry.data["dongle_id"])

        super().__init__(
            hass,
            LOGGER,
            name="MonitorySolar Coordinator",
            setup_method=self.async_setup
        )
        self.async_refresh()

    @cached_property
    def dongle_id(self) -> str:
        """ID of the inverter dongle."""
        return cast(str, self.entry.data["dongle_id"]).lower().replace("-", "_").replace(":", "_")

    @cached_property
    def inverter_brand(self) -> str:
        """The brand of the inverter."""
        return cast(str, self.entry.data["inverter_brand"])

    @property
    def firmware_code(self) -> str:
        """Firmware code of the inverter."""
        return self._firmware_code

    @callback
    async def _async_handle_mqtt_message(self, msg) -> None:
        """Manually update data and notify listeners."""
        if msg.topic == f"{self._dongle_id}/firmwarecode/response":
            LOGGER.debug("Received firmware code response")
            try:
                data = json.loads(msg.payload)
                firmware_code = data.get("FWCode")
                if firmware_code:
                    self.firmware_code = firmware_code
                    LOGGER.debug(f"Firmware code received: {self.firmware_code}")
                    self.hass.config_entries.async_update_entry(
                        self.entry, data={**self.entry.data, "firmware_code": firmware_code}
                    )
                    await self.hass.config_entries.async_forward_entry_setups(self.entry, PLATFORMS)
                else:
                    LOGGER.error("No firmware code found in response")
            except json.JSONDecodeError:
                LOGGER.error("Failed to decode JSON from response")
        elif msg.topic == f"{self._dongle_id}/response":
            await self.mqtt_handler.response_received(msg)
        elif msg.topic == f"{self._dongle_id}/status":
            await self.process_status_message(msg.payload)
        else:
            await self.process_message(msg.topic, msg.payload)
        self.async_set_updated_data(self.entities)

    @callback
    async def async_setup(self):
        """Update data via library."""
        # Initialize the MQTT handler and store it in the hass data under the domain
        mqtt_handler = MQTTHandler(self.hass)
        self.mqtt_handler = mqtt_handler
        # hass.data.setdefault(DOMAIN, {})["mqtt_handler"] = mqtt_handler

        brand_entities = ENTITIES.get(self.inverter_brand, {})
        if not brand_entities:
            LOGGER.error(f"No entities defined for inverter brand: {self.inverter_brand}")
            return False
    
        for entityTypeName, entityTypes in brand_entities.items():
            for typeName, entities in entityTypes.items():
                for entity in entities:
                    entity_id: str = f"{entityTypeName}.{self.dongle_id}_{entity['unique_id'].lower()}"
                    self.entities[entity_id] = None

        if not self.firmware_code:
            LOGGER.debug("Requesting firmware code...")
            await mqtt.async_publish(self.hass, f"{self._dongle_id}/firmwarecode/request", self._async_handle_mqtt_message)

            async def firmware_timeout(_):
                if "" == self.firmware_code:
                    LOGGER.error("Firmware code response not received within timeout")
                    await self.async_unload_entry(self.hass, self.entry)

            async_call_later(self.hass, 15, firmware_timeout)
        else:
            await self.hass.config_entries.async_forward_entry_setups(self.entry, PLATFORMS)
        self.entry.async_on_unload(self.entry.add_update_listener(self.config_entry_update_listener))
        return await mqtt.async_subscribe(self.hass, f"{self._dongle_id}/#", self._async_handle_mqtt_message)
    
    async def _async_update_data(self) -> None:
        """Update data."""
        return self.data
    
    async def config_entry_update_listener(hass: HomeAssistant, entry: MonitorMySolarEntry) -> None:
        """Update listener, called when the config entry options are changed."""
        await hass.config_entries.async_reload(entry.entry_id)

    async def async_unload_entry(hass, entry: MonitorMySolarEntry):
        """Unload a config entry."""
        LOGGER.info(f"Unloading Monitor My Solar for {entry.data.get('inverter_brand')}")
        try:
            unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
            return unload_ok
        except Exception as e:
            LOGGER.error(f"Error during unload: {e}")
            return False

    async def process_status_message(self, payload):
        """Process incoming status MQTT message and update the status sensor."""
        try:
            data = json.loads(payload)
        except ValueError:
            LOGGER.error("Invalid JSON payload received for status message")
            return

        # Check if the message follows the new structure with 'Serialnumber' and 'payload'
        if "Serialnumber" in data and "payload" in data:
            serial_number = data["Serialnumber"]
            status_data = data["payload"]
        else:
            serial_number = None  # For backward compatibility
            status_data = data  # Old format

        entity_id = f"sensor.{self.dongle_id}_uptime"
        self.entities[entity_id] = status_data

    async def process_message(self, topic, payload):
        """Process incoming MQTT message and update entity states."""
        try:
            data = json.loads(payload)
            bank_name = topic.split('/')[-1]  # Gets 'inputbank1', 'holdbank2', etc.
            self.hass.bus.async_fire(f"{DOMAIN}_bank_updated", {"bank_name": bank_name})
            
        except ValueError:
            LOGGER.error("Invalid JSON payload received")
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
            self.current_fw_version = fw_version
            # Set entity value
            entity_id = f"update.{self.dongle_id}_firmware_update"
            self.entities[entity_id] = fw_version

        # Update UI version
        if "UI_VERSION" in payload_data:
            ui_version = payload_data["UI_VERSION"]
            self.current_ui_version = ui_version
            LOGGER.debug(f"Current UI version set: {ui_version}")
            # Set entity value
            entity_id = f"update.{self.dongle_id}_ui_update"
            self.entities[entity_id] = ui_version

        # Process fault data
        if fault_data:
            LOGGER.debug(f"Processing fault data: {fault_data}")
            fault_value = fault_data.get("value", 0)
            entity_id = f"sensor.{self.dongle_id}_fault_status"
            
            if fault_value == 0:
                self.entities[entity_id] = {
                    "value": 0,
                    "description": None  # This will trigger "No Fault" state
                }
            else:
                descriptions = fault_data.get("descriptions", ["Unknown Fault"])
                timestamp = fault_data.get("timestamp", "Unknown")
                self.entities[entity_id] = {
                    "value": fault_value,
                    "description": ", ".join(descriptions),
                    "start_time": timestamp,
                    "end_time": "Ongoing"
                }

        # Process warning data
        if warning_data:
            LOGGER.debug(f"Processing warning data: {warning_data}")
            warning_value = warning_data.get("value", 0)
            entity_id = f"sensor.{self.dongle_id}_warning_status"
            
            if warning_value == 0:
                self.entities[entity_id] = {
                    "value": 0,
                    "description": None  # This will trigger "No Warning" state
                }
            else:
                descriptions = warning_data.get("descriptions", ["Unknown Warning"])
                timestamp = warning_data.get("timestamp", "Unknown")
                self.entities[entity_id] = {
                    "value": warning_value,
                    "description": ", ".join(descriptions),
                    "start_time": timestamp,
                    "end_time": "Ongoing"
                }
        # Process main sensor data
        for entity_id_suffix, state in payload_data.items():
        # Skip if we've already handled version keys
            formatted_entity_id_suffix = entity_id_suffix.lower().replace("-", "_").replace(":", "_")
            entity_type = self.determine_entity_type(formatted_entity_id_suffix)
            entity_id = f"{entity_type}.{self.dongle_id}_{formatted_entity_id_suffix}"
            self.entities[entity_id] = state
        # Process events data if present (new format)
        if events_data:
            LOGGER.debug(f"Processing events data: {events_data}")
            # Fire events for state updates
            for event_id, event_state in events_data.items():
                formatted_event_id = event_id.lower().replace("-", "_").replace(":", "_")
                entity_id = f"binary_sensor.{self.dongle_id}_{formatted_event_id}"
                self.entities[entity_id] = event_state

    def determine_entity_type(self, entity_id_suffix):
        """Determine the entity type based on the entity_id_suffix."""
        brand_entities = ENTITIES.get(self.inverter_brand, {})
        if not brand_entities:
            LOGGER.debug(f"No entities defined for inverter brand: {self.inverter_brand}. Defaulting to 'sensor'.")
            return "sensor"

        entity_id_suffix_lower = entity_id_suffix.lower()
        LOGGER.debug(f"Looking for entity_id_suffix '{entity_id_suffix_lower}' in brand '{self.inverter_brand}'.")

        for entity_type in ["sensor", "switch", "number", "time", "time_hhmm", "button", "select"]:
            if entity_type in brand_entities:
                for bank_name, entities in brand_entities[entity_type].items():
                    LOGGER.debug(f"Checking in bank '{bank_name}' for entity_type '{entity_type}'.")
                    for entity in entities:
                        unique_id_lower = entity["unique_id"].lower()
                        # LOGGER.debug(f"Comparing with unique_id '{unique_id_lower}' for entity_type '{entity_type}'.")
                        if unique_id_lower == entity_id_suffix_lower:
                            if entity_type == "time_hhmm":
                                LOGGER.debug(f"Matched entity_id_suffix '{entity_id_suffix_lower}' to entity type 'time'.")
                                return "time"
                            LOGGER.debug(f"Matched entity_id_suffix '{entity_id_suffix_lower}' to entity type '{entity_type}'.")
                            return entity_type

        LOGGER.debug(f"Could not match entity_id_suffix '{entity_id_suffix_lower}'. Defaulting to 'sensor'.")
        return "sensor"

type MonitorMySolarEntry = ConfigEntry[MonitorMySolar]