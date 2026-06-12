"""Fixtures for BGW320 tests."""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.bgw320.api import BGW320Device, BGW320RouterInfo
from custom_components.bgw320.const import DOMAIN
from homeassistant.const import CONF_HOST
from pytest_homeassistant_custom_component.common import MockConfigEntry

FIXTURE_HOST = "192.168.1.254"

MOCK_ROUTER_INFO = BGW320RouterInfo(
    mac="08:9b:b9:b2:2e:61",
    manufacturer="NOKIA",
    model="BGW320-505",
)

MOCK_DEVICES = [
    BGW320Device(
        mac="0a:0f:05:fd:1e:f4",
        hostname="Andy-s-S24",
        ip_address=None,
        connection_type="Wi-Fi",
        status="off",
    ),
    BGW320Device(
        mac="20:be:b8:ec:06:a5",
        hostname="my-phone",
        ip_address="192.168.1.201",
        connection_type="Wi-Fi",
        status="on",
    ),
]


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock BGW320 config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: FIXTURE_HOST},
        unique_id=FIXTURE_HOST,
    )


@pytest.fixture
def mock_bgw320_router() -> Iterator[AsyncMock]:
    """Patch BGW320Router so tests never hit the real network."""
    with patch(
        "custom_components.bgw320.coordinator.BGW320Router"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.get_router_info = AsyncMock(return_value=MOCK_ROUTER_INFO)
        instance.get_wifi_devices = AsyncMock(return_value=MOCK_DEVICES)
        instance.get_devices = AsyncMock(return_value=MOCK_DEVICES)
        yield instance


@pytest.fixture
def devices_html() -> str:
    """Return the fixture HTML for the BGW320 devices page."""
    return (
        Path(__file__).parent / "fixtures" / "devices.html"
    ).read_text(encoding="utf-8")


@pytest.fixture
def sysinfo_html() -> str:
    """Return the fixture HTML for the BGW320 system info page."""
    return (
        Path(__file__).parent / "fixtures" / "sysinfo.html"
    ).read_text(encoding="utf-8")
