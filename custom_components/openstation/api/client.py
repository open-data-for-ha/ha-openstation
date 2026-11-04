"""Fetches the raw OpenStation feeds. Parsing is CPU-bound and lives in parser.py."""

from __future__ import annotations

import aiohttp

from .errors import OpenStationConnectionError

# Redirect endpoints recommended by openstation-docs; the Mobilithek ids behind them
# may change, these URLs are meant not to.
NETEX_URL = "https://bahnhof.de/daten/netex"
SIRI_FM_URL = "https://bahnhof.de/daten/siri-lite/fm.xml"

NETEX_LIMIT = aiohttp.ClientTimeout(total=300)
SIRI_LIMIT = aiohttp.ClientTimeout(total=30)


class OpenStationClient:
    """Thin wrapper around the public, unauthenticated Mobilithek bulk feeds."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize with a shared session."""
        self._session = session

    async def fetch_netex(self) -> bytes:
        """Return the gzip-compressed NeTEx dataset (about 19 MB, 308 MB unpacked)."""
        return await self._fetch(NETEX_URL, NETEX_LIMIT)

    async def fetch_siri(self) -> bytes:
        """Return the gzip-compressed SIRI-FM dataset (about 30 KB)."""
        return await self._fetch(SIRI_FM_URL, SIRI_LIMIT)

    async def _fetch(self, url: str, limit: aiohttp.ClientTimeout) -> bytes:
        # Keep the body compressed: decompressing happens in the executor, and NeTEx
        # would otherwise take 308 MB of memory at once.
        try:
            async with self._session.get(
                url,
                timeout=limit,
                auto_decompress=False,
                headers={"Accept-Encoding": "gzip"},
                raise_for_status=True,
            ) as response:
                return await response.read()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise OpenStationConnectionError(f"Fetching {url} failed: {err}") from err
