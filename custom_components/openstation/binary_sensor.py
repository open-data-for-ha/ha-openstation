"""Binary sensors reporting when an elevator or escalator is out of service."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import Equipment, FacilityState, Station
from .const import CONF_STATIONS
from .coordinator import OpenStationConfigEntry, OpenStationCoordinator
from .entity import EQUIPMENT_KEYS, OUT_OF_SERVICE_ICONS, OpenStationEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OpenStationConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add one sensor per monitored equipment of the selected stations."""
    coordinator = entry.runtime_data
    entities: list[EquipmentProblemSensor] = []
    for station_id in entry.options[CONF_STATIONS]:
        station = coordinator.catalog.stations.get(station_id)
        if station is None:
            _LOGGER.warning("Station %s is no longer in the dataset", station_id)
            continue
        entities.extend(
            EquipmentProblemSensor(coordinator, station, equipment)
            for equipment in station.equipment
        )
    async_add_entities(entities)


class EquipmentProblemSensor(OpenStationEntity, BinarySensorEntity):
    """On when the equipment is reported out of service.

    Uses the problem device class because the common question is "is something
    wrong?". It is a primary entity, so it has no entity category. Its translation
    key provides the name, the state texts and the icon.
    """

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(
        self,
        coordinator: OpenStationCoordinator,
        station: Station,
        equipment: Equipment,
    ) -> None:
        """Initialize from static equipment data."""
        super().__init__(coordinator, station)
        self._equipment = equipment
        self._attr_unique_id = equipment.id
        self._attr_translation_key = EQUIPMENT_KEYS[equipment.kind]
        self._attr_translation_placeholders = {"label": station.label_of(equipment)}

    @property
    def _status(self) -> str | None:
        return self.coordinator.data.status.get(self._equipment.id)

    @property
    def available(self) -> bool:
        """Return False if the feed no longer lists this equipment."""
        return super().available and self._status is not None

    @property
    def is_on(self) -> bool | None:
        """Return True if out of service, None for unknown or unrecognized values."""
        if self._status == FacilityState.NOT_AVAILABLE:
            return True
        if self._status == FacilityState.AVAILABLE:
            return False
        return None

    @property
    def icon(self) -> str | None:
        """Return the crossed-out icon if there is no mdi: one for this kind."""
        return OUT_OF_SERVICE_ICONS.get(self._equipment.kind) if self.is_on else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return what the source states about this equipment."""
        return {
            "station": self._station.name,
            "platforms": list(self._equipment.platforms),
            "equipment_number": self._equipment.code,
            "source_status": self._status,
        }
