from homeassistant.core import HomeAssistant
from .const import LOGGER
from .coordinator import MonitorMySolar, MonitorMySolarEntry

async def async_setup_entry(hass: HomeAssistant, entry: MonitorMySolarEntry):
    # try:
    LOGGER.info(f"Setting up Monitor My Solar for {entry.data.get('inverter_brand')}")

    # Initialise the coordinator that manages data updates from mqtt.
    # This is defined in coordinator.py
    coordinator = MonitorMySolar(hass, entry)
    entry.runtime_data = coordinator

    # Perform an initial data load from mqtt.
    # async_config_entry_first_refresh() is special in that it does not log errors if it fails
    await coordinator.async_config_entry_first_refresh()

    LOGGER.info("Monitor My Solar setup completed successfully")
    return True
    # except Exception as e:
    #     LOGGER.error(f"Failed to set up Monitor My Solar: {e}")
    #     return False
