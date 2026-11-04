"""Data model of the parts of OpenStation this integration uses."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
import re
from typing import Any

# Names are German in the source, and some repeat the kind of equipment.
KIND_WORD = re.compile(
    r"^(?:personenaufzug|aufzug|fahrtreppen?|fahrsteig)\b[\s:-]*", re.IGNORECASE
)
MAIN_STATION = re.compile(r"(.+) (?:Hbf|Hauptbahnhof)")


class EquipmentKind(StrEnum):
    """NeTEx equipment types that have a realtime status in SIRI-FM."""

    LIFT = "LiftEquipment"
    ESCALATOR = "EscalatorEquipment"
    TRAVELATOR = "TravelatorEquipment"


class FacilityState(StrEnum):
    """SIRI-FM status values observed in the feed."""

    AVAILABLE = "available"
    NOT_AVAILABLE = "notAvailable"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Equipment:
    """A monitored lift, escalator or travelator."""

    id: str
    kind: EquipmentKind
    name: str
    code: str | None
    platforms: tuple[str, ...]

    @property
    def label(self) -> str:
        """Return what tells this equipment apart within its kind.

        Callers add the kind themselves, so a leading kind word in the source name
        is dropped. Some equipment has no name in the source.
        """
        return KIND_WORD.sub("", self.name).strip() or self.code or self.id[-8:]


@dataclass(frozen=True, slots=True)
class Station:
    """A station from the catalog. Main stations can have no monitored equipment."""

    id: str
    name: str
    eva: str | None
    equipment: tuple[Equipment, ...]

    def label_of(self, item: Equipment) -> str:
        """Return a label that tells item apart from its kind within this station.

        The source often names both escalators of a pair the same.
        """
        twins = sum(
            other.kind == item.kind and other.label == item.label
            for other in self.equipment
        )
        return f"{item.label} ({item.code})" if twins > 1 and item.code else item.label

    def to_dict(self) -> dict[str, Any]:
        """Serialize for the cache."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Station:
        """Restore from the cache."""
        return cls(
            id=data["id"],
            name=data["name"],
            eva=data["eva"],
            equipment=tuple(
                Equipment(
                    id=item["id"],
                    kind=EquipmentKind(item["kind"]),
                    name=item["name"],
                    code=item["code"],
                    platforms=tuple(item["platforms"]),
                )
                for item in data["equipment"]
            ),
        )


@dataclass(frozen=True, slots=True)
class StatusSnapshot:
    """One SIRI-FM delivery. Values stay raw: the source may add new ones."""

    timestamp: datetime
    status: dict[str, str]


def sort_stations(stations: Collection[Station]) -> list[Station]:
    """Sort main stations first, each group alphabetically."""
    return sorted(
        stations,
        key=lambda item: (not MAIN_STATION.fullmatch(item.name), item.name.casefold()),
    )
