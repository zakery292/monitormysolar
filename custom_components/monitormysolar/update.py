# custom_components/monitormysolar/update.py
"""Update entity for MonitorMySolar."""
from __future__ import annotations

import aiohttp
from homeassistant.components.update import (
    UpdateEntity,
    UpdateEntityFeature,
    UpdateDeviceClass,
)
from homeassistant.const import (
    STATE_UNKNOWN,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import (
    async_track_state_change_event,
)
from .const import DOMAIN, ENTITIES, LOGGER
from .coordinator import MonitorMySolarEntry
from .entity import MonitorMySolarEntity

UPDATE_URL = "https://monitoring.monitormy.solar/version"

async def async_setup_entry(hass: HomeAssistant, entry: MonitorMySolarEntry, async_add_entities) -> None:
    """Set up update entities."""
    coordinator = entry.runtime_data
    inverter_brand = coordinator.inverter_brand

    # Fetch latest versions from server
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(UPDATE_URL) as response:
                if response.status == 200:
                    server_data = await response.json()
                    coordinator.server_versions = server_data
                    LOGGER.debug(f"Update server returned: {server_data}")
                else:
                    LOGGER.error(f"Failed to fetch versions: {response.status}")
    except Exception as e:
        LOGGER.error(f"Error fetching versions: {e}")

    brand_entities = ENTITIES.get(inverter_brand, {})
    update_config = brand_entities.get("update", {})

    entities = []
    for bank_name, updates in update_config.items():
        for update in updates:
            LOGGER.debug(f"Creating update entity: {update['name']}")
            entities.append(
                InverterUpdate(
                    hass,
                    entry,
                    update["name"],
                    update["unique_id"],
                    update["version_key"],
                    update["update_command"]
                )
            )

    if entities:
        LOGGER.debug(f"Adding {len(entities)} update entities")
        async_add_entities(entities)
    else:
        LOGGER.debug("No update entities were created")

class InverterUpdate(MonitorMySolarEntity, UpdateEntity):
    """Update entity for MonitorMySolar."""

    _attr_has_entity_name = True
    _attr_supported_features = UpdateEntityFeature.INSTALL | UpdateEntityFeature.RELEASE_NOTES
    _attr_device_class = UpdateDeviceClass.FIRMWARE

    def __init__(
        self,
        hass: HomeAssistant,
        entry: MonitorMySolarEntry,
        name: str,
        unique_id: str,
        version_key: str,
        update_command: str,
    ) -> None:
        """Initialize the update entity."""
        self.coordinator = entry.runtime_data
        self.hass = hass
        self._name = name
        self._unique_id = f"{entry.entry_id}_{unique_id}"
        self._dongle_id = self.coordinator.dongle_id
        self._device_id = self.coordinator.dongle_id
        self._version_key = version_key
        self._update_command = update_command
        self._manufacturer = entry.data.get("inverter_brand")
        self.entity_id = f"update.{self._device_id}_{unique_id.lower()}"

        super().__init__(self.coordinator)

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
            return self.coordinator.current_ui_version or "Waiting..."
        return self.coordinator.current_fw_version or "Waiting..."

    @property
    def installed_version(self) -> str:
        """Get current version."""
        current_version = self._get_installed_version()
        if current_version in [None, "Waiting..."]:
            return "1.0.0"  # Default fallback
        return current_version


    def _get_latest_version(self) -> str | None:
        """Get latest version from server data."""
        server_versions = self.coordinator.server_versions or {}
        if self._version_key == "UI_VERSION":
            return server_versions.get("latestUiVersion")
        return server_versions.get("latestFwVersion")

    def _get_release_notes(self) -> str | None:
        """Get release notes from server data."""
        server_versions = self.coordinator.server_versions or {}
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
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""

        # This method is called by your DataUpdateCoordinator when a successful update runs.
        if self.entity_id in self.coordinator.entities:
            value = self.coordinator.entities[self.entity_id]
            if value is not None:
                self._attr_installed_version = value
                self.async_write_ha_state()
                # LOGGER.debug(
                #     f"Updated {self.name} installed version to: {value}"
                # )

    # async def async_added_to_hass(self):
    #     # Initial state update
    #     self._attr_installed_version = self._get_installed_version()
    #     self.async_write_ha_state()
    #     super().async_added_to_hass()

    async def async_install(
        self, version: str | None, backup: bool, **kwargs
    ) -> None:
        """Install an update."""
        LOGGER.debug(f"Install update called for {self.name}")
        mqtt_handler = self.coordinator.mqtt_handler
        if mqtt_handler:
            await mqtt_handler.send_update(
                self._dongle_id,
                self._update_command,
                1,
                self
            )
