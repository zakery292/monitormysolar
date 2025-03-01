"""Base MonitorMySolar entity."""
from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import MonitorMySolar
from .const import LOGGER

class MonitorMySolarEntity(CoordinatorEntity[MonitorMySolar]):
    """Base MonitorMySolar entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MonitorMySolar,
    ) -> None:
        # self.coordinator = coordinator
        """Initialize light."""
        super().__init__(coordinator)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        # This method is called by your DataUpdateCoordinator when a successful update runs.
        if self.entity_id in self.coordinator.entities:
            self._state = self.coordinator.entities[self.entity_id]
        else:
            LOGGER.warning(f"entity {self.entity_id} key not found")
        self.async_write_ha_state()
