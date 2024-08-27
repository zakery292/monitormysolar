import logging
import asyncio
from datetime import datetime
import json
from homeassistant.core import HomeAssistant
from homeassistant.components.mqtt import async_publish

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class MQTTHandler:
    def __init__(self, hass: HomeAssistant, use_ha_mqtt: bool):
        self.hass = hass
        self.client = None
        self.use_ha_mqtt = use_ha_mqtt
        self.processing = False  # Flag to indicate if a command is being processed
        self.command_queue = asyncio.Queue()  # Queue to hold pending commands
        self.last_time_update = None
        self.connected = False  # Track the connection status
        self.response_received_event = asyncio.Event()

    async def async_setup(self, entry):
        if self.use_ha_mqtt:
            self.client = None  # No need to assign anything here when using Home Assistant's MQTT
        else:
            import paho.mqtt.client as mqtt_client
            self.client = mqtt_client.Client()

            config = entry.data
            mqtt_server = config.get("mqtt_server", "")
            mqtt_port = config.get("mqtt_port", 1883)
            mqtt_username = config.get("mqtt_username", "")
            mqtt_password = config.get("mqtt_password", "")

            if mqtt_username:
                self.client.username_pw_set(mqtt_username, mqtt_password)

            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    _LOGGER.info("Connected to MQTT server")
                    self.connected = True
                else:
                    _LOGGER.error("Failed to connect to MQTT server, return code %d", rc)
                    self.connected = False

            def on_disconnect(client, userdata, rc):
                _LOGGER.warning("Disconnected from MQTT server")
                self.connected = False
                asyncio.run_coroutine_threadsafe(self.reconnect(), self.hass.loop)

            self.client.on_connect = on_connect
            self.client.on_disconnect = on_disconnect
            self.client.connect(mqtt_server, mqtt_port, 60)
            self.client.loop_start()

    async def reconnect(self):
        """Attempt to reconnect to the MQTT broker."""
        while not self.connected:
            try:
                _LOGGER.info("Attempting to reconnect to MQTT server...")
                self.client.reconnect()
                await asyncio.sleep(5)
            except Exception as e:
                _LOGGER.error(f"Reconnection attempt failed: {e}")
                await asyncio.sleep(10)

    async def send_update(self, dongle_id, unique_id, value, entity):
        # Rate limiting logic: only allow one update per 10 seconds
        now = datetime.now()
        if self.last_time_update and (now - self.last_time_update).total_seconds() < 10:
            _LOGGER.warning(f"Rate limit hit for {entity.entity_id}. Dropping update.")
            return

        self.last_time_update = now

        if self.processing:
            _LOGGER.info("MQTT command is already being processed. Command queued.")
            await self.command_queue.put((dongle_id, unique_id, value, entity))
            return

        self.processing = True
        try:
            await self._process_command(dongle_id, unique_id, value, entity)
        finally:
            self.processing = False
            if not self.command_queue.empty():
                next_command = await self.command_queue.get()
                await self.send_update(*next_command)

    async def _process_command(self, dongle_id, unique_id, value, entity):
        # Ensure dongle_id uses '-' instead of '_' and the characters after 'dongle-' are uppercase
        modified_dongle_id = dongle_id.replace("_", "-").split("-")
        modified_dongle_id[1] = modified_dongle_id[1].upper()
        modified_dongle_id = "-".join(modified_dongle_id)

        topic = f"{modified_dongle_id}/update"
        payload = json.dumps({unique_id: value})
        _LOGGER.debug(f"Sending MQTT update: {topic} - {payload} at {datetime.now()}")

        self.response_received_event.clear()  # Reset the event before sending the update

        def response_received(client, userdata, message):
            _LOGGER.debug(f"Received response for topic {message.topic} at {datetime.now()}: {message.payload}")
            try:
                response = json.loads(message.payload.decode())
                if response.get("status") == "success":
                    entity._state = value
                    _LOGGER.info(f"Successfully updated state of {entity.entity_id} to {value}")
                    self.hass.loop.call_soon_threadsafe(entity.async_write_ha_state)
                else:
                    _LOGGER.error(f"Failed to update state of {entity.entity_id} to {value}, reverting state.")
                    self.hass.loop.call_soon_threadsafe(entity.revert_state)
            except json.JSONDecodeError:
                _LOGGER.error(f"Failed to decode JSON response: {message.payload}")
                self.hass.loop.call_soon_threadsafe(entity.revert_state)
            finally:
                self.response_received_event.set()  # Signal that a response was received

        if self.use_ha_mqtt:
            # Home Assistant MQTT
            response_topic = f"{modified_dongle_id}/response"
            await mqtt.async_subscribe(self.hass, response_topic, response_received)
            await async_publish(self.hass, topic, payload)  # Use async_publish directly
        else:
            # Paho MQTT
            response_topic = f"{modified_dongle_id}/response"
            _LOGGER.debug(f"Subscribing to response topic: {response_topic}")
            self.client.subscribe(response_topic)
            self.client.message_callback_add(response_topic, response_received)
            self.client.publish(topic, payload)

        # Wait for the response or timeout after 5 seconds
        try:
            await asyncio.wait_for(self.response_received_event.wait(), timeout=5)
            _LOGGER.debug(f"Response received or timeout for {entity.entity_id} at {datetime.now()}")
        except asyncio.TimeoutError:
            _LOGGER.error(f"No response received for {entity.entity_id} within the timeout period.")
            self.hass.loop.call_soon_threadsafe(entity.revert_state)

