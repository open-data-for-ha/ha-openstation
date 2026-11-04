"""Base entity shared by the OpenStation platforms."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import EquipmentKind, Station
from .const import DOMAIN
from .coordinator import OpenStationCoordinator

# Translation and icon keys per kind of equipment.
EQUIPMENT_KEYS = {
    EquipmentKind.LIFT: "elevator",
    EquipmentKind.ESCALATOR: "escalator",
    EquipmentKind.TRAVELATOR: "travelator",
}

# Material Design Icons only has a crossed-out elevator, which icons.json uses. The
# others come from frontend/icons.js. They cannot go into icons.json either, because
# hassfest only allows mdi: icons there.
OUT_OF_SERVICE_ICONS = {
    EquipmentKind.ESCALATOR: f"{DOMAIN}:escalator-off",
    EquipmentKind.TRAVELATOR: f"{DOMAIN}:travelator-off",
}


def summary_key(kind: EquipmentKind) -> str:
    """Return the translation and icon key of the summary sensor of a kind."""
    return f"{EQUIPMENT_KEYS[kind]}s_out_of_service"


def summary_unique_id(station: Station, kind: EquipmentKind) -> str:
    """Return the unique_id of a summary sensor, which has no id in the source."""
    return f"{station.id}_{summary_key(kind)}"


def empty_station_unique_id(station: Station) -> str:
    """Return the unique_id of the sensor shown instead of equipment."""
    return f"{station.id}_monitored_equipment"


def station_unique_ids(station: Station) -> set[str]:
    """Return the unique_ids of all entities a station has."""
    if not station.equipment:
        return {empty_station_unique_id(station)}
    return {item.id for item in station.equipment} | {
        summary_unique_id(station, item.kind) for item in station.equipment
    }


class OpenStationEntity(CoordinatorEntity[OpenStationCoordinator]):
    """An entity on the device of its station."""

    _attr_attribution = "Data: DB InfraGO OpenStation, CC0"
    _attr_has_entity_name = True

    def __init__(self, coordinator: OpenStationCoordinator, station: Station) -> None:
        """Attach the entity to the device of its station."""
        super().__init__(coordinator)
        self._station = station
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station.id)},
            name=station.name,
            model="Station",
        )
