from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .mqttHandeler import MQTTHandler

class MonitorMySolar:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the Coordinator."""
        self.hass = hass
        self._entry = entry
        self.mqtt_handler: MQTTHandler = {}
        self.firmware_code: str = ""
        self.current_fw_version: str = ""
        self.current_ui_version: str = ""
        self.server_versions = {}