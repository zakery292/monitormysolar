import asyncio
from datetime import datetime
import json
from homeassistant.core import HomeAssistant
from homeassistant.components.mqtt import async_publish
from homeassistant.components import mqtt

from .const import DOMAIN, LOGGER

class MQTTHandler:
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.last_time_update = None
        self.response_received_event = asyncio.Event()
        self._processing = False  # To track if a command is currently being processed
        self._lock = asyncio.Lock()  # A lock to ensure only one command is processed at a time
        self.current_entity = None  # Store the current entity
        self._unsubscribe_response = None

    async def send_update(self, dongle_id, unique_id, value, entity):
        now = datetime.now()
        LOGGER.info(f"Sending update for {entity.entity_id} with value {value}")

        # Rate limiting logic: only allow one update per 1 second per entity
        if self.last_time_update and (now - self.last_time_update).total_seconds() < 1:
            LOGGER.info(f"Rate limit hit for {entity.entity_id}. Dropping update.")
            return

        async with self._lock:  # Ensure only one command is processed at a time
            if self._processing:
                LOGGER.info(f"Already processing an update for {entity.entity_id}.")
                return

            self._processing = True
            self.last_time_update = now
            self.current_entity = entity  # Store the entity to be used later in the response handling

            try:
                success = await self._process_command(dongle_id, unique_id, value, entity)
                return success
            finally:
                # Clear variables after processing the command
                self._processing = False
                self.response_received_event.clear()
                self.current_entity = None  # Clear entity after processing

    async def _process_command(self, dongle_id, unique_id, value, entity):
        modified_dongle_id = dongle_id.replace("_", "-").split("-")
        modified_dongle_id[1] = modified_dongle_id[1].upper()
        modified_dongle_id = "-".join(modified_dongle_id)

        topic = f"{modified_dongle_id}/update"
        
        # Updated payload with setting, value, and from: homeassistant
        payload = json.dumps({
            "setting": unique_id, 
            "value": value, 
            "from": "homeassistant"
        })
        
        LOGGER.info(f"Sending MQTT update: {topic} - {payload} at {datetime.now()}")
        await mqtt.async_publish(self.hass, topic, payload)

        self.response_received_event.clear()  # Reset the event before sending the update

        # Clean up any existing subscription
        if self._unsubscribe_response:
            self._unsubscribe_response()
            self._unsubscribe_response = None

        response_topic = f"{modified_dongle_id}/response"
        # Create a single subscription and store the unsubscribe function
        self._unsubscribe_response = await mqtt.async_subscribe(
            self.hass, 
            response_topic, 
            self.response_received
        )

        try:
            await asyncio.wait_for(self.response_received_event.wait(), timeout=15)
            LOGGER.debug(f"Response received or timeout for {entity.entity_id} at {datetime.now()}")
            return True
        except asyncio.TimeoutError:
            LOGGER.error(f"No response received for {entity.entity_id} within the timeout period.")
            self.hass.loop.call_soon_threadsafe(entity.revert_state)
            return False
        finally:
            # Unsubscribe from the response topic
            if self._unsubscribe_response:
                self._unsubscribe_response()
                self._unsubscribe_response = None



    async def response_received(self, msg):
        """Handle the response received message."""
        entity = self.current_entity
        if not entity:
            return

        LOGGER.info(f"Received response for topic {msg.topic} at {datetime.now()}: {msg.payload}")
        try:
            response = json.loads(msg.payload)
            
            if response.get('status') == 'success':
                LOGGER.info(f"Successfully updated state of entity {entity.entity_id}.")
                # Keep the current state as it was already optimistically updated
                self.hass.loop.call_soon_threadsafe(entity.async_write_ha_state)
            else:
                LOGGER.error(f"Failed to update state for {entity.entity_id}, reverting state.")
                self.hass.loop.call_soon_threadsafe(entity.revert_state)
        except json.JSONDecodeError:
            LOGGER.error(f"Failed to decode JSON response for {entity.entity_id}: {msg.payload}")
            self.hass.loop.call_soon_threadsafe(entity.revert_state)
        finally:
            # Unsubscribe and clear the event
            if self._unsubscribe_response:
                self._unsubscribe_response()
                self._unsubscribe_response = None
            self.response_received_event.set()




    async def send_multiple_updates(self, dongle_id, payload_dict, entity):
        """Handle multiple settings updates."""
        now = datetime.now()
        LOGGER.info(f"Sending multiple updates for {entity.entity_id} with payload {payload_dict}")

        if self.last_time_update and (now - self.last_time_update).total_seconds() < 1:
            LOGGER.info(f"Rate limit hit for {entity.entity_id}. Dropping update.")
            return

        async with self._lock:
            if self._processing:
                LOGGER.info(f"Already processing an update for {entity.entity_id}.")
                return

            self._processing = True
            self.last_time_update = now
            self.current_entity = entity

            try:
                success = await self._process_multiple_commands(dongle_id, payload_dict, entity)
                return success
            finally:
                self._processing = False
                self.response_received_event.clear()
                self.current_entity = None

    async def _process_multiple_commands(self, dongle_id, payload_dict, entity):
        """Process multiple commands in a single payload."""
        modified_dongle_id = dongle_id.replace("_", "-").split("-")
        modified_dongle_id[1] = modified_dongle_id[1].upper()
        modified_dongle_id = "-".join(modified_dongle_id)

        topic = f"{modified_dongle_id}/update"
        
        # Create payload with multiple settings
        settings = []
        for setting, value in payload_dict.items():
            settings.append({
                "setting": setting,
                "value": value
            })
        
        payload = json.dumps({
            "settings": settings,
            "from": "homeassistant"
        })
        
        LOGGER.info(f"Sending multiple MQTT updates: {topic} - {payload} at {datetime.now()}")
        await mqtt.async_publish(self.hass, topic, payload)

        self.response_received_event.clear()

        response_topic = f"{modified_dongle_id}/response"
        await mqtt.async_subscribe(self.hass, response_topic, self.response_received)

        try:
            await asyncio.wait_for(self.response_received_event.wait(), timeout=15)
            LOGGER.debug(f"Response received or timeout for {entity.entity_id} at {datetime.now()}")
            return True
        except asyncio.TimeoutError:
            LOGGER.error(f"No response received for {entity.entity_id} within the timeout period.")
            self.hass.loop.call_soon_threadsafe(entity.revert_state)
            return False