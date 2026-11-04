"""Diagnostics for OpenStation.

The integration holds no credentials or personal data. The selected stations are
public and included because they are needed to reproduce a problem.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from homeassistant.core import HomeAssistant

from .const import CONF_STATIONS
from .coordinator import OpenStationConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: OpenStationConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    snapshot = coordinator.data
    return {
        "options": dict(entry.options),
        "feed_timestamp": snapshot.timestamp.isoformat(),
        "feed_status_counts": dict(Counter(snapshot.status.values())),
        "catalog_stations": len(coordinator.catalog.stations),
        "catalog_stale": coordinator.catalog.is_stale,
        "selected_stations_missing": [
            station_id
            for station_id in entry.options[CONF_STATIONS]
            if station_id not in coordinator.catalog.stations
        ],
    }
