import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from homeassistant.helpers.event import async_call_later
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
        self.entity_id = f"switch.{dongle_id}_{sensor_info['unique_id']}"
        self.hass = hass

    # async def async_added_to_hass(self):
    #     """Call when entity is added to hass."""
    #     _LOGGER.warning(f"Adding listener for {self.entity_id}")
    #     async_call_later(self.hass, 0, self._register_listener)

    # async def _register_listener(self, _):
    #    await self.hass.bus.async_listen(f"{DOMAIN}_switch_updated", self._handle_event)

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
        _LOGGER.warning(f'Switch {self._unique_id} turned on')

    async def async_turn_off(self, **kwargs):
        self._state = False
        await self._publish_state()
        await self.async_update_ha_state()
        _LOGGER.warning(f'Switch {self._unique_id} turned off')

    async def _publish_state(self):
        """Publish state to MQTT broker."""
        topic = f"{self._dongle_id}/hold"
        payload = json.dumps({self._dongle_id: {"hold": {self._name.split('.')[1]: "on" if self._state else "off"}}})
        await async_publish(self.hass, topic, payload, qos=1, retain=True)

    @callback
    def _handle_event(self, event):
        """Handle the event."""
        _LOGGER.warning(f"Switch {self.entity_id} received event: {event.data}")
        if event.data.get("entity") == self.entity_id:
            self._state = event.data.get("value") == 'on'
            self.async_write_ha_state()

    async def async_update(self):
        """Update the switch state."""
        _LOGGER.warning(f"Updating switch {self.entity_id}")
