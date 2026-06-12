"""Device tracker platform for the BGW320 integration."""

from homeassistant.components.device_tracker import ScannerEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import (
    CONNECTION_NETWORK_MAC,
    DeviceInfo,
    format_mac,
)
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import BGW320Device
from .const import DOMAIN
from .coordinator import BGW320ConfigEntry, BGW320DataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BGW320ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up device tracker entities for the BGW320."""
    coordinator = entry.runtime_data
    tracked: set[str] = set()

    @callback
    def _add_new_entities() -> None:
        new_macs = [mac for mac in coordinator.data if mac not in tracked]
        if new_macs:
            tracked.update(new_macs)
            async_add_entities(
                BGW320ScannerEntity(coordinator, mac) for mac in new_macs
            )

    _add_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_entities))


class BGW320ScannerEntity(
    CoordinatorEntity[BGW320DataUpdateCoordinator], ScannerEntity
):
    """A device tracked by the BGW320 router."""

    def __init__(self, coordinator: BGW320DataUpdateCoordinator, mac: str) -> None:
        """Initialize the scanner entity."""
        super().__init__(coordinator)
        self._mac = mac
        self._attr_unique_id = mac

    @property
    def _device(self) -> BGW320Device | None:
        return self.coordinator.data.get(self._mac)

    @property
    def is_connected(self) -> bool:
        """Return whether the device is currently connected."""
        device = self._device
        return bool(device and device.is_connected)

    @property
    def mac_address(self) -> str:
        """Return the MAC address of the device."""
        return self._mac

    @property
    def hostname(self) -> str | None:
        """Return the hostname of the device."""
        device = self._device
        return device.hostname if device else None

    @property
    def ip_address(self) -> str | None:
        """Return the IP address of the device."""
        device = self._device
        return device.ip_address if device else None

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Disable new device tracker entities by default."""
        return False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information for this entity."""
        router_info = self.coordinator.router_info
        return DeviceInfo(
            connections={(CONNECTION_NETWORK_MAC, format_mac(self._mac))},
            name=self.hostname or self._mac,
            via_device=(DOMAIN, router_info.mac) if router_info else None,
        )

    @property
    def name(self) -> str | None:
        """Return the friendly name of the device."""
        return self.hostname
