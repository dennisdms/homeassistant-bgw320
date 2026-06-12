"""Tests for the BGW320 config flow."""

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.bgw320.api import BGW320CannotConnect
from custom_components.bgw320.const import DEFAULT_HOST, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.fixture
def mock_router_connectivity() -> AsyncMock:
    """Patch BGW320Router for config flow connectivity tests."""
    with patch(
        "custom_components.bgw320.config_flow.BGW320Router"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.get_router_info = AsyncMock(return_value=None)
        yield instance


async def test_user_step_success(
    hass: HomeAssistant,
    mock_router_connectivity: AsyncMock,
    mock_bgw320_router: AsyncMock,
) -> None:
    """Test a successful user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.254"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "BGW320 (192.168.1.254)"
    assert result["data"] == {CONF_HOST: "192.168.1.254"}


async def test_user_step_cannot_connect(
    hass: HomeAssistant,
    mock_router_connectivity: AsyncMock,
) -> None:
    """Test config flow when the router is unreachable."""
    mock_router_connectivity.get_router_info.side_effect = BGW320CannotConnect("timeout")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.254"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_step_unknown_error(
    hass: HomeAssistant,
    mock_router_connectivity: AsyncMock,
) -> None:
    """Test config flow when an unexpected error occurs."""
    mock_router_connectivity.get_router_info.side_effect = Exception("boom")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.254"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_user_step_already_configured(
    hass: HomeAssistant,
    mock_router_connectivity: AsyncMock,
) -> None:
    """Test that a duplicate host is rejected."""
    existing = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.254"},
        unique_id="192.168.1.254",
    )
    existing.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.254"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
