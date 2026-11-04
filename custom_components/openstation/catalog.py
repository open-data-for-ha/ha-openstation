"""Cached catalog of stations, built from the NeTEx dataset."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .api import OpenStationClient, Station, parse_netex
from .const import CATALOG_MAX_AGE, DOMAIN

STORAGE_VERSION = 1


class StationCatalog:
    """Stations with monitored equipment, kept in HA storage between restarts."""

    def __init__(self, hass: HomeAssistant, client: OpenStationClient) -> None:
        """Initialize an empty catalog."""
        self._hass = hass
        self._client = client
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.stations"
        )
        self.stations: dict[str, Station] = {}
        self._fetched_at: datetime | None = None

    @classmethod
    def create(cls, hass: HomeAssistant) -> StationCatalog:
        """Create a catalog using Home Assistant's shared session."""
        return cls(hass, OpenStationClient(async_get_clientsession(hass)))

    @property
    def is_stale(self) -> bool:
        """Return whether the catalog is due for a refresh."""
        return (
            self._fetched_at is None
            or dt_util.utcnow() - self._fetched_at > CATALOG_MAX_AGE
        )

    async def async_load(self) -> None:
        """Load from storage, or fetch if nothing has been stored yet."""
        if stored := await self._store.async_load():
            self._fetched_at = dt_util.parse_datetime(stored["fetched_at"])
            self.stations = {
                item["id"]: Station.from_dict(item) for item in stored["stations"]
            }
        else:
            await self.async_refresh()

    async def async_refresh(self) -> None:
        """Fetch NeTEx and replace the catalog; keeps the old one on failure."""
        data = await self._client.fetch_netex()
        stations = await self._hass.async_add_executor_job(parse_netex, data)
        self.stations = stations
        self._fetched_at = dt_util.utcnow()
        await self._store.async_save(
            {
                "fetched_at": self._fetched_at.isoformat(),
                "stations": [item.to_dict() for item in stations.values()],
            }
        )
