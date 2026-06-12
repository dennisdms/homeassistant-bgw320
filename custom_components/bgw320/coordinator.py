"""DataUpdateCoordinator for the BGW320 integration."""

from dataclasses import replace
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BGW320CannotConnect, BGW320Device, BGW320Router, BGW320RouterInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)

type BGW320ConfigEntry = ConfigEntry[BGW320DataUpdateCoordinator]


class BGW320DataUpdateCoordinator(DataUpdateCoordinator[dict[str, BGW320Device]]):
    """Coordinator that polls the BGW320 router for connected Wi-Fi devices."""

    config_entry: BGW320ConfigEntry
    router_info: BGW320RouterInfo | None

    def __init__(self, hass: HomeAssistant, entry: BGW320ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            config_entry=entry,
        )
        self.router = BGW320Router(
            async_get_clientsession(hass),
            entry.data[CONF_HOST],
        )
        self.router_info = None

    async def _async_update_data(self) -> dict[str, BGW320Device]:
        """Fetch the current list of Wi-Fi connected devices."""
        try:
            if self.router_info is None:
                info = await self.router.get_router_info()
                self.router_info = replace(info, mac=format_mac(info.mac))
            devices = await self.router.get_wifi_devices()
        except BGW320CannotConnect as err:
            raise UpdateFailed(str(err)) from err
        return {
            (mac := format_mac(device.mac)): replace(device, mac=mac)
            for device in devices
        }
