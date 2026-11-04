"""Parsers for OpenStation NeTEx and SIRI-FM.

Both functions block and must run in an executor.
"""

from __future__ import annotations

from datetime import datetime
import gzip
import io
import xml.etree.ElementTree as ET

from .errors import OpenStationParseError
from .models import MAIN_STATION, Equipment, EquipmentKind, Station, StatusSnapshot

NETEX = "{http://www.netex.org.uk/netex}"
SIRI = "{http://www.siri.org.uk/siri}"
GZIP_MAGIC = b"\x1f\x8b"
EQ_ID_NAMESPACE = "https://daten.bahnhof.de/namespace/eq/"
PLATFORM = "railIslandPlatform"


def _open(data: bytes) -> io.BufferedIOBase:
    """Return a stream over data, decompressing lazily to keep memory flat."""
    stream = io.BytesIO(data)
    if data.startswith(GZIP_MAGIC):
        return gzip.GzipFile(fileobj=stream)
    return stream


def _read_name(element: ET.Element | None) -> str:
    """Read a Name. Inline text disappears on 2027-04-01, Text children stay."""
    if element is None:
        return ""
    texts = element.findall(f"{NETEX}Text")
    for text in texts:
        if text.get("lang") == "de" and text.text:
            return text.text.strip()
    if texts and texts[0].text:
        return texts[0].text.strip()
    return (element.text or "").strip()


def _read_code(element: ET.Element) -> str | None:
    """Read the EQ-ID. The standalone PrivateCode disappears on 2027-04-01."""
    for code in element.iterfind(f"{NETEX}privateCodes/{NETEX}PrivateCode"):
        if code.get("type") == EQ_ID_NAMESPACE and code.text:
            return code.text
    return element.findtext(f"{NETEX}PrivateCode")


def _read_key(element: ET.Element, key: str) -> str | None:
    for entry in element.iterfind(f"{NETEX}keyList/{NETEX}KeyValue"):
        if entry.findtext(f"{NETEX}Key") == key:
            return entry.findtext(f"{NETEX}Value")
    return None


def _platforms_by_equipment(stop: ET.Element) -> dict[str, list[str]]:
    """Map equipment ids to the names of the platforms that reference them.

    All references observed so far sit directly on platforms. ParentQuayRef is followed
    anyway because the source models edges and sectors as child quays. Across the
    network, path links and access spaces did not resolve any lift that this direct
    route misses.
    """
    quays = {
        quay.get("id"): quay for quay in stop.iterfind(f"{NETEX}quays/{NETEX}Quay")
    }
    result: dict[str, list[str]] = {}
    for quay in quays.values():
        platform: ET.Element | None = quay
        seen: set[str | None] = set()
        while (
            platform is not None and platform.findtext(f"{NETEX}QuayType") != PLATFORM
        ):
            seen.add(platform.get("id"))
            parent = platform.find(f"{NETEX}ParentQuayRef")
            ref = parent.get("ref") if parent is not None else None
            platform = quays.get(ref) if ref not in seen else None
        if platform is None:
            continue
        name = _read_name(platform.find(f"{NETEX}Name"))
        for ref_element in quay.iterfind(
            f"{NETEX}equipmentPlaces/{NETEX}EquipmentPlace/{NETEX}placeEquipments/*"
        ):
            if (ref := ref_element.get("ref")) and name not in result.get(ref, []):
                result.setdefault(ref, []).append(name)
    return result


def _parse_stop(stop: ET.Element) -> Station | None:
    platforms = _platforms_by_equipment(stop)
    equipment: list[Equipment] = []
    for kind in EquipmentKind:
        for item in stop.iterfind(f"{NETEX}placeEquipments/{NETEX}{kind.value}"):
            equipment_id = item.get("id")
            if not equipment_id:
                continue
            equipment.append(
                Equipment(
                    id=equipment_id,
                    kind=kind,
                    name=_read_name(item.find(f"{NETEX}Name")),
                    code=_read_code(item),
                    platforms=tuple(sorted(platforms.get(equipment_id, []))),
                )
            )
    stop_id = stop.get("id")
    name = _read_name(stop.find(f"{NETEX}Name"))
    if not stop_id or not (equipment or MAIN_STATION.fullmatch(name)):
        return None
    return Station(
        id=stop_id,
        name=name,
        eva=_read_key(stop, "EVA"),
        equipment=tuple(equipment),
    )


def parse_netex(data: bytes) -> dict[str, Station]:
    """Return stations with monitored equipment and all main stations, by StopPlace id.

    Main stations stay findable when the source lists no equipment for them.
    """
    stations: dict[str, Station] = {}
    try:
        with _open(data) as stream:
            for _, element in ET.iterparse(stream, events=("end",)):
                if element.tag == f"{NETEX}StopPlace":
                    if station := _parse_stop(element):
                        stations[station.id] = station
                    element.clear()
    except (ET.ParseError, OSError, EOFError) as err:
        raise OpenStationParseError(f"Invalid NeTEx data: {err}") from err
    if not any(station.equipment for station in stations.values()):
        raise OpenStationParseError("NeTEx data contains no monitored equipment")
    return stations


def parse_siri(data: bytes) -> StatusSnapshot:
    """Return the status of every facility in a SIRI-FM delivery."""
    try:
        with _open(data) as stream:
            root = ET.parse(stream).getroot()
        raw = root.findtext(f"{SIRI}ServiceDelivery/{SIRI}ResponseTimestamp")
        if raw is None:
            raise OpenStationParseError("SIRI-FM data has no ResponseTimestamp")
        timestamp = datetime.fromisoformat(raw)
    except (ET.ParseError, OSError, EOFError, ValueError) as err:
        raise OpenStationParseError(f"Invalid SIRI-FM data: {err}") from err

    status: dict[str, str] = {}
    for condition in root.iter(f"{SIRI}FacilityCondition"):
        ref = condition.findtext(f"{SIRI}FacilityRef")
        value = condition.findtext(f"{SIRI}FacilityStatus/{SIRI}Status")
        if ref and value:
            status[ref] = value
    return StatusSnapshot(timestamp=timestamp, status=status)
