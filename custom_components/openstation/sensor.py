"""Sensors summarizing the equipment of a station by kind."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import Equipment, EquipmentKind, FacilityState, Station
from .const import CONF_STATIONS
from .coordinator import OpenStationConfigEntry, OpenStationCoordinator
from .entity import (
    EQUIPMENT_KEYS,
    OUT_OF_SERVICE_ICONS,
    OpenStationEntity,
    empty_station_unique_id,
    summary_key,
    summary_unique_id,
)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OpenStationConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add a summary per kind of equipment, or a note if a station has none."""
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = []
    for station_id in entry.options[CONF_STATIONS]:
        station = coordinator.catalog.stations.get(station_id)
        if station is None:
            continue
        if not station.equipment:
            entities.append(NoEquipmentSensor(coordinator, station))
        entities.extend(
            OutOfServiceSensor(coordinator, station, kind)
            for kind in EQUIPMENT_KEYS
            if any(item.kind == kind for item in station.equipment)
        )
    async_add_entities(entities)


class NoEquipmentSensor(OpenStationEntity, SensorEntity):
    """Shows that the source monitors nothing at a station.

    Home Assistant lists no device without an entity, so selecting such a station
    would otherwise look like a failure.
    """

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_value = 0
    _attr_translation_key = "monitored_equipment"

    def __init__(self, coordinator: OpenStationCoordinator, station: Station) -> None:
        """Initialize for a station without equipment."""
        super().__init__(coordinator, station)
        self._attr_unique_id = empty_station_unique_id(station)


class OutOfServiceSensor(OpenStationEntity, SensorEntity):
    """Counts equipment of one kind that is reported out of service.

    Equipment without a usable status is listed separately, because many reports are
    unknown and a bare count would suggest more certainty than the data holds.
    """

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: OpenStationCoordinator,
        station: Station,
        kind: EquipmentKind,
    ) -> None:
        """Initialize from the static equipment of the station."""
        super().__init__(coordinator, station)
        self._equipment = [item for item in station.equipment if item.kind == kind]
        self._attr_unique_id = summary_unique_id(station, kind)
        self._attr_translation_key = summary_key(kind)
        self._attr_icon = OUT_OF_SERVICE_ICONS.get(kind)

    def _with_status(self, *states: FacilityState) -> list[Equipment]:
        status = self.coordinator.data.status
        return [item for item in self._equipment if status.get(item.id) in states]

    @property
    def native_value(self) -> int | None:
        """Return the count, or None if no equipment has a usable status."""
        out_of_service = self._with_status(FacilityState.NOT_AVAILABLE)
        if out_of_service or self._with_status(FacilityState.AVAILABLE):
            return len(out_of_service)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return which equipment the count is about."""
        out_of_service = self._with_status(FacilityState.NOT_AVAILABLE)
        known = out_of_service + self._with_status(FacilityState.AVAILABLE)
        return {
            "out_of_service": [self._station.label_of(item) for item in out_of_service],
            "unknown": [
                self._station.label_of(item)
                for item in self._equipment
                if item not in known
            ],
            "affected_platforms": sorted(
                {platform for item in out_of_service for platform in item.platforms}
            ),
            "total": len(self._equipment),
        }
