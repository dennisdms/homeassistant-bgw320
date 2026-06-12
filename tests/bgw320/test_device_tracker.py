"""Tests for the BGW320 device tracker platform."""

import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from pytest_homeassistant_custom_component.common import MockConfigEntry

from .conftest import MOCK_DEVICES


@pytest.mark.usefixtures("mock_bgw320_router")
async def test_device_tracker_entities_created(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """WiFi devices become tracker entities, disabled by default."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_reg = er.async_get(hass)
    entries = er.async_entries_for_config_entry(
        entity_reg, mock_config_entry.entry_id
    )
    assert len(entries) == len(MOCK_DEVICES)
    assert all(entry.disabled for entry in entries)


@pytest.mark.usefixtures("mock_bgw320_router")
async def test_device_tracker_is_connected(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Entity reflects the router status (on → home, off → not_home)."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_reg = er.async_get(hass)
    for entry in er.async_entries_for_config_entry(
        entity_reg, mock_config_entry.entry_id
    ):
        entity_reg.async_update_entity(entry.entity_id, disabled_by=None)
    await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # MOCK_DEVICES[0]: status=off → not_home
    state_off = hass.states.get("device_tracker.andy_s_s24")
    assert state_off is not None
    assert state_off.state == "not_home"

    # MOCK_DEVICES[1]: status=on → home
    state_on = hass.states.get("device_tracker.my_phone")
    assert state_on is not None
    assert state_on.state == "home"


@pytest.mark.usefixtures("mock_bgw320_router")
async def test_device_tracker_attributes(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Entity exposes mac, ip, and host_name state attributes."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_reg = er.async_get(hass)
    for entry in er.async_entries_for_config_entry(
        entity_reg, mock_config_entry.entry_id
    ):
        entity_reg.async_update_entity(entry.entity_id, disabled_by=None)
    await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.my_phone")
    assert state is not None
    assert state.attributes["ip"] == "192.168.1.201"
    assert state.attributes["mac"] == "20:be:b8:ec:06:a5"
    assert state.attributes["host_name"] == "my-phone"


@pytest.mark.usefixtures("mock_bgw320_router")
async def test_device_tracker_snapshot(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    snapshot: SnapshotAssertion,
) -> None:
    """Snapshot all tracker entity registry entries."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_reg = er.async_get(hass)
    entries = er.async_entries_for_config_entry(
        entity_reg, mock_config_entry.entry_id
    )
    assert entries == snapshot
