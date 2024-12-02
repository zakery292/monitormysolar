# custom_components/monitormysolar/update.py
"""Update entity for MonitorMySolar."""
from __future__ import annotations

import logging
import aiohttp
from homeassistant.components.update import (
    UpdateEntity,
    UpdateEntityFeature,
    UpdateDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN, ENTITIES

_LOGGER = logging.getLogger(__name__)

UPDATE_URL = "https://monitoring.monitormy.solar/version"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up update entities."""
    inverter_brand = entry.data.get("inverter_brand")
    dongle_id = entry.data.get("dongle_id").lower().replace("-", "_")

    _LOGGER.info(f"Setting up update entities for {inverter_brand}")

    # Fetch latest versions from server
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(UPDATE_URL) as response:
                if response.status == 200:
                    server_data = await response.json()
                    hass.data[DOMAIN]["server_versions"] = server_data
                    _LOGGER.debug(f"Update server returned: {server_data}")
                else:
                    _LOGGER.error(f"Failed to fetch versions: {response.status}")
    except Exception as e:
        _LOGGER.error(f"Error fetching versions: {e}")

    brand_entities = ENTITIES.get(inverter_brand, {})
    update_config = brand_entities.get("update", {})

    entities = []
    for bank_name, updates in update_config.items():
        for update in updates:
            _LOGGER.debug(f"Creating update entity: {update['name']}")
            entities.append(
                InverterUpdate(
                    hass,
                    entry,
                    update["name"],
                    update["unique_id"],
                    dongle_id,
                    update["version_key"],
                    update["update_command"]
                )
            )

    if entities:
        _LOGGER.debug(f"Adding {len(entities)} update entities")
        async_add_entities(entities)
    else:
        _LOGGER.warning("No update entities were created")

class InverterUpdate(UpdateEntity):
    """Update entity for MonitorMySolar."""

    _attr_has_entity_name = True
    _attr_supported_features = UpdateEntityFeature.INSTALL | UpdateEntityFeature.RELEASE_NOTES
    _attr_device_class = UpdateDeviceClass.FIRMWARE

    def __init__(
        self, 
        hass: HomeAssistant,
        entry: ConfigEntry,
        name: str,
        unique_id: str,
        dongle_id: str,
        version_key: str,
        update_command: str,
    ) -> None:
        """Initialize the update entity."""
        self.hass = hass
        self._name = name
        self._unique_id = f"{entry.entry_id}_{unique_id}"
        self._dongle_id = dongle_id.lower().replace("-", "_")
        self._device_id = dongle_id.lower().replace("-", "_")
        self._version_key = version_key
        self._update_command = update_command
        self._manufacturer = entry.data.get("inverter_brand")
        self.entity_id = f"update.{self._device_id}_{unique_id.lower()}"
        
        # Set initial versions
        self._attr_installed_version = self._get_installed_version()
        self._attr_latest_version = self._get_latest_version()
        self._attr_release_summary = self._get_release_notes()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._dongle_id)},
            "name": f"Inverter {self._dongle_id}",
            "manufacturer": self._manufacturer,
        }

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id
    
    def _get_installed_version(self) -> str:
        """Get current installed version from domain data."""
        if self._version_key == "UI_VERSION":
            return self.hass.data[DOMAIN].get("current_ui_version", "Waiting...")
        return self.hass.data[DOMAIN].get("current_fw_version", "Waiting...")

    @property
    def installed_version(self) -> str:
        """Get current version."""
        current_version = self._get_installed_version()
        if current_version in [None, "Waiting..."]:
            return "1.0.0"  # Default fallback
        return current_version


    def _get_latest_version(self) -> str | None:
        """Get latest version from server data."""
        server_versions = self.hass.data[DOMAIN].get("server_versions", {})
        if self._version_key == "UI_VERSION":
            return server_versions.get("latestUiVersion")
        return server_versions.get("latestFwVersion")

    def _get_release_notes(self) -> str | None:
        """Get release notes from server data."""
        server_versions = self.hass.data[DOMAIN].get("server_versions", {})
        changelog = server_versions.get("changelog")
        if not changelog:
            return None
            
        if "UI:" in changelog and "FW:" in changelog:
            parts = changelog.split("FW:")
            ui_part = parts[0].replace("UI:", "").strip()
            fw_part = parts[1].strip()
            
            return ui_part if self._version_key == "UI_VERSION" else fw_part
        return changelog
    @property
    def latest_version(self) -> str | None:
        """Get latest version."""
        latest = self._get_latest_version()
        if latest is None:
            return "Checking..."
        return latest
    @callback
    def _handle_version_update(self, event):
        """Handle version update events."""
        event_entity_id = event.data.get("entity").lower().replace("-", "_")
        if event_entity_id == self.entity_id:
            value = event.data.get("value")
            if value is not None:
                self._attr_installed_version = value
                self.async_write_ha_state()
                _LOGGER.debug(
                    f"Updated {self.name} installed version to: {value}"
                )

    async def async_added_to_hass(self):
        """Subscribe to events when added to hass."""
        self.hass.bus.async_listen(f"{DOMAIN}_update_version", self._handle_version_update)
        # Initial state update
        self._attr_installed_version = self._get_installed_version()
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        """Unsubscribe from events when removed."""
        self.hass.bus._async_remove_listener(f"{DOMAIN}_update_version", self._handle_version_update)

    async def async_install(
        self, version: str | None, backup: bool, **kwargs
    ) -> None:
        """Install an update."""
        _LOGGER.debug(f"Install update called for {self.name}")
        mqtt_handler = self.hass.data[DOMAIN].get("mqtt_handler")
        if mqtt_handler:
            await mqtt_handler.send_update(
                self._dongle_id,
                self._update_command,
                1,
                self
            )