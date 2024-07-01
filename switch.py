# switch.py
import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.mqtt import async_publish
from .const import DOMAIN, SENSORS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    inverter_brand = entry.data.get("inverter_brand")
    dongle_id = entry.data.get("dongle_id")
    switches = [sensor for sensor in SENSORS.get(inverter_brand, []) if sensor["type"] == "switch"]

    entities = [InverterSwitch(sensor, entry, dongle_id, hass) for sensor in switches]
    async_add_entities(entities, True)

class InverterSwitch(SwitchEntity):
    def __init__(self, sensor_info, entry, dongle_id, hass):
        self._name = sensor_info["name"]
        self._unique_id = f"{entry.entry_id}_{sensor_info['unique_id']}"
        self._state = False
        self._dongle_id = dongle_id
        self.hass = hass

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def is_on(self):
        return self._state

    async def async_turn_on(self, **kwargs):
        self._state = True
        await self._publish_state()
        await self.async_update_ha_state()

    async def async_turn_off(self, **kwargs):
        self._state = False
        await self._publish_state()
        await self.async_update_ha_state()

    async def _publish_state(self):
        """Publish state to MQTT broker."""
        topic = f"{self._dongle_id}/hold"
        payload = json.dumps({self._dongle_id: {"hold": {self._name: "on" if self._state else "off"}}})
        await async_publish(self.hass, topic, payload, qos=1, retain=True)

    async def async_update(self):
        # Here you could add code to fetch the latest state from the device if needed
        pass
