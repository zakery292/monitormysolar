import logging
import asyncio
import json
from homeassistant.core import HomeAssistant
from homeassistant.components import mqtt

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class MQTTHandler:
    def __init__(self, hass: HomeAssistant, use_ha_mqtt: bool):
        self.hass = hass
        self.client = None
        self.use_ha_mqtt = use_ha_mqtt

    async def async_setup(self, entry):
        if self.use_ha_mqtt:
            # Use Home Assistant's MQTT component directly
            self.client = mqtt
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
                else:
                    _LOGGER.error(
                        "Failed to connect to MQTT server, return code %d", rc
                    )

            self.client.on_connect = on_connect
            self.client.connect(mqtt_server, mqtt_port, 60)
            self.client.loop_start()

    async def send_update(self, dongle_id, unique_id, value, entity):
        # Ensure dongle_id uses '-' instead of '_' and the characters after 'dongle-' are uppercase
        modified_dongle_id = dongle_id.replace("_", "-").split("-")
        modified_dongle_id[1] = modified_dongle_id[1].upper()
        modified_dongle_id = "-".join(modified_dongle_id)

        topic = f"{modified_dongle_id}/update"
        payload = json.dumps({unique_id: value})
        _LOGGER.warning(f"Sending MQTT update: {topic} - {payload}")

        if self.use_ha_mqtt:
            await self.client.async_publish(self.hass, topic, payload)
        else:
            self.client.publish(topic, payload)

        def response_received(client, userdata, message):
            _LOGGER.warning(
                f"Received response for topic {message.topic}: {message.payload}"
            )
            if message.payload.decode() == "success":
                entity._state = value
                entity.async_write_ha_state()
            else:
                entity.revert_state()

        if not self.use_ha_mqtt:
            response_topic = f"{modified_dongle_id}/response"
            self.client.subscribe(response_topic)
            self.client.message_callback_add(response_topic, response_received)
