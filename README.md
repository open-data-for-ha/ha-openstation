# Öffentliche Bahnhofsdaten for Home Assistant

An unofficial custom integration that shows whether elevators, escalators and travelators
at German railway stations are working, using DB InfraGO's open
[OpenStation](https://github.com/dbinfrago/openstation-docs) data. Searching for
"OpenStation" finds it in Home Assistant as well.

## What it does and does not do

It adds one device for each station you pick, with one binary sensor for each elevator,
escalator and travelator there. Sensors are named and shown with an icon by type, such as
"Elevator zu Gleis 5/6". Descriptions come from the source in German. Where the source links an elevator to a platform, the sensor lists
that platform.

It does not tell you whether a track is reachable step-free or plan a route, and it does
not cover stations outside DB InfraGO's network.

## Requirements

- Home Assistant 2026.10.4 or newer
- [HACS](https://hacs.xyz/) for the recommended installation
- Internet access. No account or API key is needed.

## Installation

### HACS

1. In HACS, open the menu and choose **Custom repositories**.
2. Add `https://github.com/open-data-for-ha/ha-openstation` with the type **Integration**.
3. Install **Öffentliche Bahnhofsdaten** and restart Home Assistant.

### Manual

Copy `custom_components/openstation` into your Home Assistant `custom_components` folder
and restart.

## Configuration

Go to **Settings > Devices & services > Add integration** and search for
**Öffentliche Bahnhofsdaten** or **OpenStation**. Then pick your stations. The first run downloads the station
list, which can take a minute.

The station list shows main stations first, also while you type a city name.

To add or remove a station later, open **Settings > Devices & services > Öffentliche
Bahnhofsdaten** and choose **Configure**. There is no separate add button: all stations share
one entry, so that the source is polled only once. The same dialog sets the polling
interval (60 to 3600 seconds, default 300).

## Entities

| Shown as | State | Meaning |
| --- | --- | --- |
| In service | `off` | Reported as working |
| Out of service | `on` | Reported as out of service |
| Unknown | `unknown` | The source does not know the status |
| Unavailable | `unavailable` | The source lists no status for it, or the feed is over 30 minutes old |

Attributes: `station`, `platforms`, `equipment_number` and `source_status`.

Icons always show the type of equipment. Colors come from Home Assistant, which only
marks out of service in red. For green when in service and gray when unknown, add a theme
and select it in your user profile:

```yaml
# configuration.yaml
frontend:
  themes:
    OpenStation:
      state-binary_sensor-problem-off-color: var(--green-color)
      state-binary_sensor-problem-unknown-color: var(--grey-color)
```

This applies to every `problem` sensor in Home Assistant, not only to this integration.
Tile cards use these colors by default, entities cards need `state_color: true`, and the
device page shows no state colors.

To get these colors with the default theme as well, in light and dark mode, save this as
`www/openstation-colors.js` in your configuration folder:

```js
const style = document.createElement("style");
style.textContent = `html {
  --state-binary_sensor-problem-off-color: var(--green-color);
  --state-binary_sensor-problem-unknown-color: var(--grey-color);
}`;
document.head.append(style);
```

Then load it in `configuration.yaml` and restart Home Assistant:

```yaml
frontend:
  extra_module_url:
    - /local/openstation-colors.js
```

Restart Home Assistant, then clear the browser cache. A normal reload can keep showing
the old colors because the frontend caches its start page. The same applies after
changing the file.

Each station also gets a sensor counting what is out of service, one per type of equipment
it has, such as "Elevators out of service". Use it to be alerted about a whole station.

| Attribute | Meaning |
| --- | --- |
| `out_of_service` | The equipment that is counted |
| `unknown` | Equipment without a usable status, which is not counted |
| `affected_platforms` | Platforms linked to that equipment; other routes may still exist |
| `total` | All equipment of this type at the station |

A count of 0 only covers equipment with a known status, so check `unknown` as well. If no
equipment has a usable status, the sensor shows Unknown.

## Data source and license

Station and status data comes from OpenStation by DB InfraGO AG, released under
[CC0](https://creativecommons.org/publicdomain/zero/1.0/) and fetched from
[Mobilithek](https://mobilithek.info/offers/930558234532405248). The code in this
repository is under the MIT license.

## Disclaimer

Unofficial community project, not affiliated with or endorsed by Deutsche Bahn AG / DB
InfraGO AG. Status data may be delayed or incomplete; do not rely on it as the sole basis
for safety-relevant travel decisions.

## Known limitations

- Status updated irregularly when measured, 50 seconds to 7 minutes apart, so a change can
  take that long to appear, plus your polling interval.
- Some main stations have no monitored equipment in the source, among them München Hbf,
  Bochum Hbf and Kassel Hbf. They are marked (0) in the station list and show a note instead
  of sensors. Other stops without monitored equipment are not listed.
- The source does not list every elevator. Frankfurt (Main) Hbf had 2 in the data, while
  bahnhof.de showed about 10 when compared.
- About 8 % of elevators have no platform link in the source. Their names often still say
  where they lead.
- Some equipment has no name in the source and is shown with its number. About 5 % of
  equipment reported `unknown` when measured.
- Status correctness has not been checked against the actual equipment.
- Equipment added to a station appears after the next reload of the integration.
- The first setup downloads and parses a 19 MB file. This has not been measured on small
  hardware such as a Raspberry Pi.
