"""Tests for the BGW320 API (HTML parsing)."""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.bgw320.api import (
    BGW320CannotConnect,
    BGW320Device,
    BGW320Router,
    BGW320RouterInfo,
    _DeviceParser,
    _SysinfoParser,
)


def test_device_parser_wifi_and_ethernet(devices_html: str) -> None:
    """Parser extracts all devices from the fixture HTML."""
    parser = _DeviceParser()
    parser.feed(devices_html)
    parser.close()

    assert len(parser.devices) == 3

    macs = {d.mac for d in parser.devices}
    assert macs == {
        "04:7c:16:49:37:40",
        "0a:0f:05:fd:1e:f4",
        "20:be:b8:ec:06:a5",
    }


def test_device_parser_wired_device(devices_html: str) -> None:
    """Ethernet device is parsed correctly and is_wifi returns False."""
    parser = _DeviceParser()
    parser.feed(devices_html)
    parser.close()

    wired = next(d for d in parser.devices if d.mac == "04:7c:16:49:37:40")
    assert wired.hostname == "pop-os"
    assert wired.ip_address == "192.168.1.175"
    assert wired.status == "on"
    assert not wired.is_wifi


def test_device_parser_wifi_no_ip(devices_html: str) -> None:
    """Wi-Fi device without an IP is parsed correctly."""
    parser = _DeviceParser()
    parser.feed(devices_html)
    parser.close()

    device = next(d for d in parser.devices if d.mac == "0a:0f:05:fd:1e:f4")
    assert device.hostname == "Andy-s-S24"
    assert device.ip_address is None
    assert device.status == "off"
    assert device.is_wifi
    assert not device.is_connected


def test_device_parser_wifi_with_ip(devices_html: str) -> None:
    """Wi-Fi device with an IP is parsed correctly."""
    parser = _DeviceParser()
    parser.feed(devices_html)
    parser.close()

    device = next(d for d in parser.devices if d.mac == "20:be:b8:ec:06:a5")
    assert device.hostname == "my-phone"
    assert device.ip_address == "192.168.1.201"
    assert device.status == "on"
    assert device.is_wifi
    assert device.is_connected


async def test_router_get_wifi_devices_filters_wired(devices_html: str) -> None:
    """get_wifi_devices returns only Wi-Fi devices."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.text = AsyncMock(return_value=devices_html)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_resp)

    router = BGW320Router(mock_session, "192.168.1.254")
    devices = await router.get_wifi_devices()

    assert len(devices) == 2
    assert all(d.is_wifi for d in devices)


async def test_router_cannot_connect_on_client_error() -> None:
    """BGW320CannotConnect is raised on aiohttp errors."""
    mock_session = MagicMock()
    mock_session.get = MagicMock(side_effect=aiohttp.ClientError("refused"))

    router = BGW320Router(mock_session, "192.168.1.254")
    with pytest.raises(BGW320CannotConnect):
        await router.get_devices()


def test_sysinfo_parser(sysinfo_html: str) -> None:
    """Parser extracts manufacturer, model, and MAC from the sysinfo page."""
    parser = _SysinfoParser()
    parser.feed(sysinfo_html)
    parser.close()

    info = parser.router_info
    assert info is not None
    assert info.manufacturer == "NOKIA"
    assert info.model == "BGW320-505"
    assert info.mac == "08:9b:b9:b2:2e:61"


async def test_router_get_router_info(sysinfo_html: str) -> None:
    """get_router_info returns a populated BGW320RouterInfo."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.text = AsyncMock(return_value=sysinfo_html)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_resp)

    router = BGW320Router(mock_session, "192.168.1.254")
    info = await router.get_router_info()

    assert isinstance(info, BGW320RouterInfo)
    assert info.mac == "08:9b:b9:b2:2e:61"
    assert info.manufacturer == "NOKIA"
    assert info.model == "BGW320-505"


async def test_router_cannot_connect_on_bad_status() -> None:
    """BGW320CannotConnect is raised on non-200 HTTP responses."""
    mock_resp = MagicMock()
    mock_resp.status = 500
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_resp)

    router = BGW320Router(mock_session, "192.168.1.254")
    with pytest.raises(BGW320CannotConnect):
        await router.get_devices()
