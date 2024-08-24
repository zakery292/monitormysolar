import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.core import callback
from .const import DOMAIN, ENTITIES, FIRMWARE_CODES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    inverter_brand = entry.data.get("inverter_brand")
    dongle_id = entry.data.get("dongle_id").lower().replace("-", "_")
    firmware_code = entry.data.get("firmware_code")
    device_type = FIRMWARE_CODES.get(firmware_code, {}).get("Device_Type", "")
    sw_version = entry.data.get("sw_version")
    latest_firmware_version = entry.data.get("latest_firmware_version")

    brand_entities = ENTITIES.get(inverter_brand, {})
    buttons_config = brand_entities.get("buttons", {})

    entities = []
    for bank_name, buttons in buttons_config.items():
        for button in buttons:
            try:
                entities.append(
                    FirmwareUpdateButton(button, hass, entry, dongle_id, bank_name, sw_version, latest_firmware_version)
                )
            except Exception as e:
                _LOGGER.error(f"Error setting up button {button}: {e}")

    async_add_entities(entities, True)
class FirmwareUpdateButton(ButtonEntity):
    def __init__(self, button_info, hass, entry, dongle_id, bank_name, sw_version, latest_firmware_version):
        """Initialize the button."""
        _LOGGER.debug(f"Initializing button with info: {button_info}")
        self.button_info = button_info
        self._name = button_info["name"]
        self._unique_id = f"{entry.entry_id}_{button_info['unique_id']}".lower()
        self._dongle_id = dongle_id.lower().replace("-", "_")
        self._device_id = dongle_id.lower().replace("-", "_")
        self._button_type = button_info["unique_id"]
        self._bank_name = bank_name
        self.entity_id = f"button.{self._device_id}_{self._button_type.lower()}"
        self.hass = hass
        self._manufacturer = entry.data.get("inverter_brand")
        self._sw_version = sw_version
        self._latest_firmware_version = latest_firmware_version

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._dongle_id)},
            "name": f"Inverter {self._dongle_id}",
            "manufacturer": f"{self._manufacturer}",
        }

    async def async_press(self):
        """Handle the button press."""
        if self._sw_version < self._latest_firmware_version:
            # Firmware update is needed
            _LOGGER.info(f"Firmware update button pressed for {self._dongle_id}")
            topic = f"{self._dongle_id}/update"
            payload = "updatedongle"
            self.hass.components.mqtt.async_publish(self.hass, topic, payload)
            _LOGGER.info(f"Firmware update request sent to {topic} with payload {payload}")
        else:
            # No update needed
            _LOGGER.info(f"No firmware update needed for {self._dongle_id}. SW_VERSION: {self._sw_version}, LatestFirmwareVersion: {self._latest_firmware_version}")
            hass.bus.async_fire(f"{DOMAIN}_notification", {
                "title": "Firmware Update",
                "message": "No update available for the dongle."
            })

