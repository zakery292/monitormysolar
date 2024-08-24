import logging
from homeassistant.components.select import SelectEntity
from homeassistant.core import callback
from .const import DOMAIN, ENTITIES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    inverter_brand = entry.data.get("inverter_brand")
    dongle_id = entry.data.get("dongle_id").lower().replace("-", "_")
    brand_entities = ENTITIES.get(inverter_brand, {})
    select_config = brand_entities.get("select", {})

    entities = []
    for bank_name, selects in select_config.items():
        for select in selects:
            try:
                entities.append(InverterSelect(select, hass, entry, dongle_id))
            except Exception as e:
                _LOGGER.error(f"Error setting up select {select}: {e}")

    async_add_entities(entities, True)


class InverterSelect(SelectEntity):
    def __init__(self, entity_info, hass, entry, dongle_id):
        """Initialize the select entity."""
        _LOGGER.debug(f"Initializing select with info: {entity_info}")
        self.entity_info = entity_info
        self._name = entity_info["name"]
        self._unique_id = f"{entry.entry_id}_{entity_info['unique_id']}".lower()
        self._state = None
        self._dongle_id = dongle_id.lower().replace("-", "_")
        self._device_id = dongle_id.lower().replace("-", "_")
        self._entity_type = entity_info["unique_id"]
        self.entity_id = f"select.{self._device_id}_{self._entity_type.lower()}"
        self.hass = hass
        self._options = entity_info["options"]
        self._manufacturer = entry.data.get("inverter_brand")

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def current_option(self):
        return self._state

    @property
    def options(self):
        return self._options

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._dongle_id)},
            "name": f"Inverter {self._dongle_id}",
            "manufacturer": f"{self._manufacturer}",
        }

    async def async_select_option(self, option):
        """Update the select option."""
        _LOGGER.info(f"Setting select option for {self.entity_id} to {option}")
        self._state = option
        self.async_write_ha_state()
        bit_value = self._options.index(option)
        await self.hass.data[DOMAIN]["mqtt_handler"].send_update(
            self._dongle_id.replace("_", "-"),
            self.entity_info["unique_id"],
            bit_value,
            self,
        )

    def revert_state(self):
        """Revert to the previous state."""
        _LOGGER.info(f"Reverting state for {self.entity_id} to {self._state}")
        self.async_write_ha_state()

    @callback
    def _handle_event(self, event):
        """Handle the event."""
        _LOGGER.debug(f"Handling event for select {self.entity_id}: {event.data}")
        event_entity_id = event.data.get("entity").lower().replace("-", "_")
        if event_entity_id == self.entity_id:
            value = event.data.get("value")
            _LOGGER.debug(f"Received event for select {self.entity_id}: {value}")
            if value is not None:
                self._state = (
                    self._options[value]
                    if isinstance(value, int) and value < len(self._options)
                    else value
                )
                _LOGGER.debug(f"Select {self.entity_id} state updated to {self._state}")
                self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        _LOGGER.debug(f"Select {self.entity_id} added to hass")
        self.hass.bus.async_listen(f"{DOMAIN}_select_updated", self._handle_event)
        _LOGGER.debug(f"Select {self.entity_id} subscribed to event")
