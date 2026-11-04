"""Polling coordinator for the SIRI-FM status feed."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import OpenStationClient, OpenStationError, StatusSnapshot, parse_siri
from .catalog import StationCatalog
from .const import CATALOG_RETRY_DELAY, DEFAULT_SCAN_INTERVAL, DOMAIN, MAX_FEED_AGE

_LOGGER = logging.getLogger(__name__)

type OpenStationConfigEntry = ConfigEntry[OpenStationCoordinator]


class OpenStationCoordinator(DataUpdateCoordinator[StatusSnapshot]):
    """Fetches realtime status and keeps the static catalog fresh."""

    config_entry: OpenStationConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: OpenStationConfigEntry,
        client: OpenStationClient,
        catalog: StationCatalog,
    ) -> None:
        """Initialize the coordinator with the interval from the options."""
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )
        self._client = client
        self.catalog = catalog
        self._next_catalog_attempt = datetime.min.replace(tzinfo=UTC)

    async def _async_update_data(self) -> StatusSnapshot:
        now = dt_util.utcnow()
        if self.catalog.is_stale and now >= self._next_catalog_attempt:
            self._next_catalog_attempt = now + CATALOG_RETRY_DELAY
            self.config_entry.async_create_background_task(
                self.hass, self._async_refresh_catalog(), f"{DOMAIN} catalog refresh"
            )
        try:
            data = await self._client.fetch_siri()
            snapshot = await self.hass.async_add_executor_job(parse_siri, data)
        except OpenStationError as err:
            raise UpdateFailed(str(err)) from err
        if now - snapshot.timestamp > MAX_FEED_AGE:
            raise UpdateFailed(f"Feed is stale, last update {snapshot.timestamp}")
        return snapshot

    async def _async_refresh_catalog(self) -> None:
        """Refresh the catalog. Status keeps working on the old one if this fails."""
        try:
            await self.catalog.async_refresh()
        except OpenStationError as err:
            _LOGGER.warning("Could not refresh station catalog: %s", err)
