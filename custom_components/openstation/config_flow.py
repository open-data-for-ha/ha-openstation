"""Config flow for OpenStation: pick stations once, change them in the options."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
import probatio

from .api import MAIN_STATION, OpenStationError, Station, sort_stations
from .catalog import StationCatalog
from .const import (
    CONF_STATIONS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

# The search in the picker ranks names with fewer words higher, and it only treats
# U+0020 and U+00A0 as word separators. This space looks the same but keeps a main
# station at one word, level with names like "Dresden-Dobritz". Ties keep the list
# order, which starts with the main stations.
LABEL_SPACE = "\u2005"


def _station_label(station: Station) -> str:
    label = station.name if station.equipment else f"{station.name} (0)"
    if MAIN_STATION.fullmatch(station.name):
        return label.replace(" ", LABEL_SPACE)
    return label


def _station_selector(catalog: StationCatalog) -> SelectSelector:
    options = [
        SelectOptionDict(value=station.id, label=_station_label(station))
        for station in sort_stations(catalog.stations.values())
    ]
    return SelectSelector(
        SelectSelectorConfig(
            options=options, multiple=True, mode=SelectSelectorMode.DROPDOWN
        )
    )


class OpenStationConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OpenStationOptionsFlow:
        """Return the options flow."""
        return OpenStationOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user pick stations. The first run downloads the catalog."""
        catalog = StationCatalog.create(self.hass)
        try:
            await catalog.async_load()
        except OpenStationError:
            return self.async_abort(reason="cannot_connect")

        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_STATIONS]:
                return self.async_create_entry(
                    title="Öffentliche Bahnhofsdaten",
                    data={},
                    options={
                        CONF_STATIONS: user_input[CONF_STATIONS],
                        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                    },
                )
            errors["base"] = "no_stations"

        return self.async_show_form(
            step_id="user",
            data_schema=probatio.Schema(
                {probatio.Required(CONF_STATIONS): _station_selector(catalog)}
            ),
            errors=errors,
        )


class OpenStationOptionsFlow(OptionsFlowWithReload):
    """Change the stations and the polling interval."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the options form."""
        catalog = StationCatalog.create(self.hass)
        try:
            await catalog.async_load()
        except OpenStationError:
            return self.async_abort(reason="cannot_connect")

        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_STATIONS]:
                return self.async_create_entry(
                    data={
                        CONF_STATIONS: user_input[CONF_STATIONS],
                        CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
                    }
                )
            errors["base"] = "no_stations"

        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=probatio.Schema(
                {
                    probatio.Required(
                        CONF_STATIONS, default=options[CONF_STATIONS]
                    ): _station_selector(catalog),
                    probatio.Required(
                        CONF_SCAN_INTERVAL,
                        default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            max=MAX_SCAN_INTERVAL,
                            step=60,
                            unit_of_measurement="s",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
            errors=errors,
        )
