import logging
from datetime import datetime, time
from homeassistant.components.datetime import DateTimeEntity
from homeassistant.components.time import TimeEntity
from homeassistant.core import callback
from .const import DOMAIN, ENTITIES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    inverter_brand = entry.data.get("inverter_brand")
    dongle_id = entry.data.get("dongle_id").lower().replace("-", "_")
    brand_entities = ENTITIES.get(inverter_brand, {})

    entities = []

    # Setup DateTime entities
    time_config = brand_entities.get("time", {})
    for bank_name, time_entities in time_config.items():
        for time_entity in time_entities:
            if "timestamp" in time_entity.get("device_class", ""):
                try:
                    entities.append(
                        InverterDateTime(time_entity, hass, entry, dongle_id)
                    )
                except Exception as e:
                    _LOGGER.error(f"Error setting up time entity {time_entity}: {e}")
            else:
                try:
                    entities.append(InverterTime(time_entity, hass, entry, dongle_id))
                except Exception as e:
                    _LOGGER.error(
                        f"Error setting up time HHMM entity {time_entity}: {e}"
                    )

    async_add_entities(entities, True)


class InverterDateTime(DateTimeEntity):
    def __init__(self, entity_info, hass, entry, dongle_id):
        """Initialize the DateTime entity."""
        _LOGGER.debug(f"Initializing DateTime entity with info: {entity_info}")
        self.entity_info = entity_info
        self._name = entity_info["name"]
        self._unique_id = f"{entry.entry_id}_{entity_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = dongle_id.lower().replace("-", "_")
        self._device_id = dongle_id.lower().replace("-", "_")
        self._entity_type = entity_info["unique_id"]
        self.entity_id = f"datetime.{self._device_id}_{self._entity_type.lower()}"
        self.hass = hass
        self._attr_native_value = entity_info.get("native_value")
        self._attr_icon = entity_info.get("icon", "mdi:calendar-clock")
        self._manufacturer = entry.data.get("inverter_brand")

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def native_value(self):
        return self._attr_native_value

    @property
    def icon(self):
        return self._attr_icon

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

    async def async_set_value(self, value: datetime):
        """Update the current date and time."""
        _LOGGER.debug(f"Setting date and time for {self.entity_id} to {value}")
        await self.hass.data[DOMAIN]["mqtt_handler"].send_update(
            self._dongle_id.replace("_", "-"),
            self.entity_info["unique_id"],
            value.isoformat(),
            self,
        )

    def revert_state(self):
        """Revert to the previous state."""
        self.async_write_ha_state()

    @callback
    def _handle_event(self, event):
        """Handle the event."""
        _LOGGER.debug(f"Handling event for datetime {self.entity_id}: {event.data}")
        event_entity_id = event.data.get("entity").lower().replace("-", "_")
        if event_entity_id == self.entity_id:
            value = event.data.get("value")
            _LOGGER.debug(f"Received event for datetime {self.entity_id}: {value}")
            if value is not None:
                self._attr_native_value = datetime.fromisoformat(value)
                _LOGGER.debug(f"DateTime {self.entity_id} state updated to {value}")
                self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        _LOGGER.debug(f"DateTime {self.entity_id} added to hass")
        self.hass.bus.async_listen(f"{DOMAIN}_datetime_updated", self._handle_event)
        _LOGGER.debug(f"DateTime {self.entity_id} subscribed to event")


class InverterTime(DateTimeEntity):
    def __init__(self, entity_info, hass, entry, dongle_id):
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
        """Set the time value."""
        _LOGGER.debug(f"Setting time value for {self.entity_id} to {value}")
        await self.hass.data[DOMAIN]["mqtt_handler"].send_update(
            self._dongle_id.replace("_", "-"),
            self.entity_info["unique_id"],
            value.isoformat(),
            self,
        )

    def revert_state(self):
        """Revert to the previous state."""
        self.async_write_ha_state()

    @callback
    def _handle_event(self, event):
        """Handle the event."""
        _LOGGER.debug(f"Handling event for time {self.entity_id}: {event.data}")
        event_entity_id = event.data.get("entity").lower().replace("-", "_")
        if event_entity_id == self.entity_id:
            value = event.data.get("value")
            _LOGGER.debug(f"Received event for time {self.entity_id}: {value}")
            if value is not None:
                self._state = value
                _LOGGER.debug(f"Time {self.entity_id} state updated to {value}")
                self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        _LOGGER.debug(f"Time {self.entity_id} added to hass")
        self.hass.bus.async_listen(f"{DOMAIN}_time_updated", self._handle_event)
        _LOGGER.debug(f"Time {self.entity_id} subscribed to event")
