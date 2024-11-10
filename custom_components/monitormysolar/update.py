"""Update entity for MonitorMySolar."""
from __future__ import annotations

import logging
import aiohttp
import async_timeout
from datetime import timedelta

from homeassistant.components.update import (
    UpdateEntity,
    UpdateEntityFeature,
    UpdateDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
UPDATE_URL = "https://monitoring.monitormy.solar/version"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the update entity."""
    coordinator = UpdateCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()
    
    async_add_entities([
        DongleFirmwareUpdate(coordinator, entry),
        DongleUIUpdate(coordinator, entry)
    ])

class UpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching update data."""

    def __init__(self, hass: HomeAssistant):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=24),  # Check once per day
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        async with async_timeout.timeout(10):
            async with aiohttp.ClientSession() as session:
                async with session.get(UPDATE_URL) as response:
                    response.raise_for_status()
                    return await response.json()

class DongleFirmwareUpdate(UpdateEntity):
    """Firmware update entity for MonitorMySolar dongle."""

    _attr_supported_features = (
        UpdateEntityFeature.INSTALL 
        | UpdateEntityFeature.RELEASE_NOTES
    )
    _attr_device_class = UpdateDeviceClass.FIRMWARE

    def __init__(self, coordinator: UpdateCoordinator, entry: ConfigEntry):
        """Initialize the update entity."""
        self.coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_firmware_update"
        self._attr_title = "MonitorMySolar Dongle Firmware"
        self._attr_has_entity_name = True
    @property
    def installed_version(self) -> str | None:
        """Version currently installed and in use."""
        state = self.hass.states.get(f"sensor.{self._entry.entry_id}_sw_version")
        return state.state if state else None

    @property
    def latest_version(self) -> str | None:
        """Latest version available for install."""
        if self.coordinator.data:
            return self.coordinator.data.get("latestFwVersion")
        return None

    @property
    def release_summary(self) -> str | None:
        """Return the release summary."""
        if self.coordinator.data:
            return self.coordinator.data.get("changelog")
        return None

    async def async_install(self, version: str | None, backup: bool, **kwargs) -> None:
        """Install the update."""
        mqtt_handler = self.hass.data[DOMAIN].get("mqtt_handler")
        if mqtt_handler:
            # Send update command via MQTT
            await mqtt_handler.send_update(
                self._entry.data["dongle_id"],
                "update_firmware",
                1,
                self
            )

class DongleUIUpdate(UpdateEntity):
    """UI update entity for MonitorMySolar dongle."""

    _attr_supported_features = (
        UpdateEntityFeature.INSTALL 
        | UpdateEntityFeature.RELEASE_NOTES
    )
    _attr_device_class = UpdateDeviceClass.FIRMWARE

    def __init__(self, coordinator: UpdateCoordinator, entry: ConfigEntry):
        """Initialize the update entity."""
        self.coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_ui_update"
        self._attr_title = "MonitorMySolar Dongle UI"
        self._attr_has_entity_name = True

    @property
    def installed_version(self) -> str | None:
        """Version currently installed and in use."""
        state = self.hass.states.get(f"sensor.{self._entry.entry_id}_ui_version")
        return state.state if state else None

    @property
    def latest_version(self) -> str | None:
        """Latest version available for install."""
        if self.coordinator.data:
            return self.coordinator.data.get("latestUiVersion")
        return None

    @property
    def release_summary(self) -> str | None:
        """Return the release summary."""
        if self.coordinator.data:
            return self.coordinator.data.get("changelog")
        return None

    async def async_install(self, version: str | None, backup: bool, **kwargs) -> None:
        """Install the update."""
        mqtt_handler = self.hass.data[DOMAIN].get("mqtt_handler")
        if mqtt_handler:
            # Send update command via MQTT
            await mqtt_handler.send_update(
                self._entry.data["dongle_id"],
                "update_ui",
                1,
                self
            )