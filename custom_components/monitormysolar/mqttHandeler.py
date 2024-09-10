import logging
import asyncio
from datetime import datetime
import json
from homeassistant.core import HomeAssistant
from homeassistant.components.mqtt import async_publish
from homeassistant.components import mqtt

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class MQTTHandler:
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.last_time_update = None
        self.response_received_event = asyncio.Event()
        self._processing = False  # To track if a command is currently being processed
        self._lock = asyncio.Lock()  # A lock to ensure only one command is processed at a time

    async def async_setup(self, entry):
        self.hass.data[DOMAIN]["mqtt_handler"] = self

    async def send_update(self, dongle_id, unique_id, value, entity):
        now = datetime.now()
        _LOGGER.info(f"Sending update for {entity.entity_id} with value {value}")

        # Rate limiting logic: only allow one update per 10 seconds per entity
        if self.last_time_update and (now - self.last_time_update).total_seconds() < 5:
            _LOGGER.info(f"Rate limit hit for {entity.entity_id}. Dropping update.")
            return

        async with self._lock:  # Ensure only one command is processed at a time
            if self._processing:
                _LOGGER.info(f"Already processing an update for {entity.entity_id}.")
                return

            self._processing = True
            self.last_time_update = now

            try:
                success = await self._process_command(dongle_id, unique_id, value, entity)
                return success
            finally:
                # Clear variables after processing the command
                self._processing = False
                self.response_received_event.clear()

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
        
        _LOGGER.info(f"Sending MQTT update: {topic} - {payload} at {datetime.now()}")
        await mqtt.async_publish(self.hass, topic, payload)

        self.response_received_event.clear()  # Reset the event before sending the update

        response_topic = f"{modified_dongle_id}/response"
        await mqtt.async_subscribe(self.hass, response_topic, self.response_received)

        try:
            await asyncio.wait_for(self.response_received_event.wait(), timeout=15)
            _LOGGER.debug(f"Response received or timeout for {entity.entity_id} at {datetime.now()}")
            return True
        except asyncio.TimeoutError:
            _LOGGER.error(f"No response received for {entity.entity_id} within the timeout period.")
            self.hass.loop.call_soon_threadsafe(entity.revert_state)
            return False

    async def response_received(self, msg):
        _LOGGER.info(f"Received response for topic {msg.topic} at {datetime.now()}: {msg.payload}")
        try:
            response = json.loads(msg.payload)
            
            # Check if 'payload' and 'status' exist in the response
            if 'payload' in response and response['payload'].get('status') == 'success':
                _LOGGER.info(f"Successfully updated state of entity.")
            else:
                _LOGGER.error(f"Failed to update state, reverting state.")
                self.hass.loop.call_soon_threadsafe(self._revert_state)
        except json.JSONDecodeError:
            _LOGGER.error(f"Failed to decode JSON response: {msg.payload}")
            self.hass.loop.call_soon_threadsafe(self._revert_state)
        finally:
            self.response_received_event.set()


    def _revert_state(self, entity):
        """Revert the state of the entity in case of failure."""
        entity.revert_state()
