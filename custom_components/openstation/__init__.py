"""The OpenStation integration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .api import OpenStationClient, OpenStationError
from .catalog import StationCatalog
from .const import CONF_STATIONS, DOMAIN, ICONS_URL
from .coordinator import OpenStationConfigEntry, OpenStationCoordinator
from .entity import station_unique_ids

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the custom icons, once per run, as entries can reload."""
    integration = await async_get_integration(hass, DOMAIN)
    await hass.http.async_register_static_paths(
        [StaticPathConfig(ICONS_URL, str(Path(__file__).parent / "frontend/icons.js"))]
    )
    # The version makes browsers fetch a new file after an update.
    add_extra_js_url(hass, f"{ICONS_URL}?v={integration.version}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: OpenStationConfigEntry) -> bool:
    """Set up OpenStation from a config entry."""
    client = OpenStationClient(async_get_clientsession(hass))
    catalog = StationCatalog(hass, client)
    try:
        await catalog.async_load()
    except OpenStationError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = OpenStationCoordinator(hass, entry, client, catalog)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    _async_remove_stale_entries(hass, entry, catalog)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: OpenStationConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _async_remove_stale_entries(
    hass: HomeAssistant, entry: OpenStationConfigEntry, catalog: StationCatalog
) -> None:
    """Remove deselected stations and equipment that left the dataset."""
    stations = [
        station
        for station_id in entry.options[CONF_STATIONS]
        if (station := catalog.stations.get(station_id))
    ]

    wanted_devices = {(DOMAIN, station.id) for station in stations}
    device_registry = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
        if not device.identifiers & wanted_devices:
            _LOGGER.debug("Removing stale device %s", device.name)
            device_registry.async_update_device(
                device.id, remove_config_entry_id=entry.entry_id
            )

    wanted_entities = set().union(*map(station_unique_ids, stations))
    entity_registry = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if entity.unique_id not in wanted_entities:
            _LOGGER.debug("Removing stale entity %s", entity.entity_id)
            entity_registry.async_remove(entity.entity_id)
