"""Constants for the OpenStation integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "openstation"

CONF_STATIONS: Final = "stations"

ICONS_URL: Final = f"/{DOMAIN}/icons.js"

# The feed advanced irregularly, 50 to 420 s apart, when measured, so this interval can
# lag by a few minutes.
DEFAULT_SCAN_INTERVAL: Final = 300
MIN_SCAN_INTERVAL: Final = 60
MAX_SCAN_INTERVAL: Final = 3600

# NeTEx changes rarely and is 19 MB compressed, so fetch it at most daily.
CATALOG_MAX_AGE: Final = timedelta(hours=24)
# Spacing between attempts, so a failing refresh does not repeat with every poll.
CATALOG_RETRY_DELAY: Final = timedelta(hours=1)
# A feed this old is stuck; showing its data as current would mislead users.
MAX_FEED_AGE: Final = timedelta(minutes=30)
