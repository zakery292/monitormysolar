import logging
from datetime import datetime, timedelta
import asyncio
from homeassistant.components.time import TimeEntity
from homeassistant.core import callback
from .const import DOMAIN, ENTITIES
from . import MonitorMySolarEntry

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    inverter_brand = entry.data.get("inverter_brand")
    dongle_id = entry.data.get("dongle_id").lower().replace("-", "_")
    brand_entities = ENTITIES.get(inverter_brand, {})

    entities = []

    # Setup Time entities
    time_config = brand_entities.get("time", {})
    for bank_name, time_entities in time_config.items():
        for time_entity in time_entities:
            entities.append(InverterTime(time_entity, hass, entry, dongle_id))

    async_add_entities(entities, True)

class InverterTime(TimeEntity):
    def __init__(self, entity_info, hass, entry: MonitorMySolarEntry, dongle_id):
        """Initialize the Time entity."""
        _LOGGER.debug(f"Initializing Time entity with info: {entity_info}")
        self.entity_info = entity_info
        self._name = entity_info["name"]
        self._unique_id = f"{entry.entry_id}_{entity_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = dongle_id.lower().replace("-", "_")
        self._device_id = dongle_id.lower().replace("-", "_")
        self._entity_type = entity_info["unique_id"]
        self.entity_id = f"time.{self._device_id}_{self._entity_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._last_mqtt_update = None
        self._debounce_task = None
        self.coordinator = entry.runtime_data

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._state

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._dongle_id)},
            "name": f"Inverter {self._dongle_id}",
            "manufacturer": f"{self._manufacturer}",
        }

    async def async_set_value(self, value):
        """Handle user input and send to MQTT."""
        now = datetime.now()

        # Check if the state has changed
        if self._state == value or self._state is None:
            _LOGGER.debug(f"No change in state for {self.entity_id}. Skipping MQTT update.")
            return

        # Debounce logic to delay the MQTT update and prevent multiple messages
        if self._debounce_task:
            self._debounce_task.cancel()

        async def debounce():
            await asyncio.sleep(1)
            if self._last_mqtt_update and (now - self._last_mqtt_update).total_seconds() < 1:
                _LOGGER.debug(f"Skipping MQTT update for {self.entity_id} due to rate limiting")
                return

            _LOGGER.info(f"Setting time value for {self.entity_id} to {value}")
            self.update_state(value)
            await self.coordinator.mqtt_handler.send_update(
                self._dongle_id.replace("_", "-"),
                self.entity_info["unique_id"],
                value.isoformat(),
                self,
            )

        self._debounce_task = asyncio.create_task(debounce())

    @callback
    def update_state(self, value):
        """Update the state without triggering MQTT (e.g., from MQTT message)."""
        if self._state != value:
            self._state = value
            self._last_mqtt_update = datetime.now()
            _LOGGER.debug(f"Time {self.entity_id} state updated to {value}")
            # Schedule state update on the main thread
            self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)

    def revert_state(self):
        """Revert to the previous state."""
        # Schedule state revert on the main thread
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)

    @callback
    def _handle_event(self, event):
        """Handle the event."""
        # _LOGGER.debug(f"Handling event for time {self.entity_id}: {event.data}")  # Ensure comments are well-formed
        event_entity_id = event.data.get("entity").lower().replace("-", "_")
        if event_entity_id == self.entity_id:
            value = event.data.get("value")
            # _LOGGER.debug(f"Received event for time {self.entity_id}: {value}")  # Ensure comments are well-formed
            if value is not None:
                self.update_state(value)

    async def async_will_remove_from_hass(self):
        """Unsubscribe from events when removed."""
        _LOGGER.debug(f"Time {self.entity_id} will be removed from hass")
        self.hass.bus._async_remove_listener(f"{DOMAIN}_time_updated", self._handle_event)

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        #_LOGGER.debug(f"Time {self.entity_id} added to hass")
        self.hass.bus.async_listen(f"{DOMAIN}_time_updated", self._handle_event)
        #_LOGGER.debug(f"Time {self.entity_id} subscribed to event")
