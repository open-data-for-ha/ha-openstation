# Öffentliche Bahnhofsdaten für Home Assistant

*The English version of this README follows below the German one: [English](#english).*

Eine inoffizielle Custom-Integration, die anzeigt, ob Aufzüge, Rolltreppen und Fahrsteige an
deutschen Bahnhöfen funktionieren. Grundlage sind die offenen
[OpenStation](https://github.com/dbinfrago/openstation-docs)-Daten der DB InfraGO. Auch die
Suche nach „OpenStation“ findet die Integration in Home Assistant.

## Was sie kann und was nicht

Sie legt für jeden gewählten Bahnhof ein Gerät an, mit einem binären Sensor je Aufzug,
Rolltreppe und Fahrsteig. Sensoren tragen Name und Icon ihres Typs, zum Beispiel „Aufzug zu
Gleis 5/6“. Die Beschreibungen stammen aus der Quelle. Verknüpft die Quelle einen Aufzug mit
einem Bahnsteig, nennt der Sensor diesen Bahnsteig.

Sie sagt nicht, ob ein Gleis stufenfrei erreichbar ist, plant keine Routen und deckt keine
Bahnhöfe außerhalb des Netzes der DB InfraGO ab.

## Voraussetzungen

- Home Assistant 2026.10.4 oder neuer
- Internetzugang. Für die Integration sind weder Konto noch API-Schlüssel nötig. Nur das
  Hinzufügen über einen Link im Marketplace verlangt eine Verbindung mit GitHub.
- Unter Home Assistant 2026.10 zusätzlich [HACS](https://hacs.xyz/). Ab 2026.11 ist es als
  Marketplace eingebaut.

## Installation

### Marketplace (ab Home Assistant 2026.11)

1. Öffne **Einstellungen > Marketplace** und wähle **Über Link hinzufügen**. Verbinde dich mit
   GitHub, falls du danach gefragt wirst.
2. Gib `https://github.com/open-data-for-ha/ha-openstation` mit dem Typ **Integration** ein.
3. Installiere **Öffentliche Bahnhofsdaten** und starte Home Assistant neu.

Hast du die Integration schon über HACS installiert, übernimmt Home Assistant sie beim Update
auf 2026.11 von selbst.

### HACS (Home Assistant 2026.10)

1. Öffne in HACS das Menü und wähle **Benutzerdefinierte Repositories** (**Custom
   repositories**).
2. Füge `https://github.com/open-data-for-ha/ha-openstation` mit dem Typ **Integration**
   hinzu.
3. Installiere **Öffentliche Bahnhofsdaten** und starte Home Assistant neu.

### Manuell

Kopiere `custom_components/openstation` in den Ordner `custom_components` deiner
Home-Assistant-Konfiguration und starte neu.

## Einrichtung

Gehe zu **Einstellungen > Geräte & Dienste > Integration hinzufügen** und suche nach
**Öffentliche Bahnhofsdaten** oder **OpenStation**. Wähle dann deine Bahnhöfe. Beim ersten
Mal wird die Bahnhofsliste geladen, das kann eine Minute dauern.

Die Liste zeigt Hauptbahnhöfe zuerst, auch während du einen Stadtnamen tippst.

Um später Bahnhöfe hinzuzufügen oder zu entfernen, öffne **Einstellungen > Geräte & Dienste >
Öffentliche Bahnhofsdaten** und wähle **Konfigurieren**. Einen eigenen Button zum Hinzufügen
gibt es nicht: Alle Bahnhöfe teilen sich einen Eintrag, damit die Quelle nur einmal abgefragt
wird. Im selben Dialog stellst du das Abfrageintervall ein (60 bis 3600 Sekunden, Standard
300).

## Entitäten

| Anzeige | Zustand | Bedeutung |
| --- | --- | --- |
| In Betrieb | `off` | Als funktionierend gemeldet |
| Außer Betrieb | `on` | Als außer Betrieb gemeldet |
| Unbekannt | `unknown` | Die Quelle kennt den Status nicht |
| Nicht verfügbar | `unavailable` | Die Quelle nennt keinen Status, oder der Feed ist älter als 30 Minuten |

Attribute: `station`, `platforms`, `equipment_number` und `source_status`.

Jeder Bahnhof bekommt außerdem je Anlagentyp einen Sensor, der zählt, was außer Betrieb ist,
zum Beispiel „Aufzüge außer Betrieb“. Damit lässt sich ein ganzer Bahnhof überwachen.

| Attribut | Bedeutung |
| --- | --- |
| `out_of_service` | Die gezählten Anlagen |
| `unknown` | Anlagen ohne verwertbaren Status, die nicht mitgezählt werden |
| `affected_platforms` | Bahnsteige dieser Anlagen; andere Wege können trotzdem existieren |
| `total` | Alle Anlagen dieses Typs am Bahnhof |

Eine 0 gilt nur für Anlagen mit bekanntem Status, prüfe also auch `unknown`. Hat keine Anlage
einen verwertbaren Status, zeigt der Sensor „Unbekannt“.

### Icons und Farben

Icons zeigen immer den Anlagentyp und sind durchgestrichen, wenn die Anlage außer Betrieb ist.
Die Farben kommen von Home Assistant, das nur „Außer Betrieb“ rot markiert. Für Grün bei „In
Betrieb“ und Grau bei „Unbekannt“ lege ein Theme an und wähle es in deinem Benutzerprofil aus:

```yaml
# configuration.yaml
frontend:
  themes:
    OpenStation:
      state-binary_sensor-problem-off-color: var(--green-color)
      state-binary_sensor-problem-unknown-color: var(--grey-color)
```

Das gilt für alle `problem`-Sensoren in Home Assistant, nicht nur für diese Integration.
Tile-Karten nutzen diese Farben von selbst, Entities-Karten brauchen `state_color: true`, und
die Geräteseite zeigt keine Zustandsfarben.

Für dieselben Farben im Standard-Theme, hell wie dunkel, speichere dies als
`www/openstation-colors.js` in deinem Konfigurationsordner:

```js
const style = document.createElement("style");
style.textContent = `html {
  --state-binary_sensor-problem-off-color: var(--green-color);
  --state-binary_sensor-problem-unknown-color: var(--grey-color);
}`;
document.head.append(style);
```

Binde die Datei dann in der `configuration.yaml` ein:

```yaml
frontend:
  extra_module_url:
    - /local/openstation-colors.js
```

Starte Home Assistant neu und leere danach den Browser-Cache. Ein normales Neuladen kann
weiter die alten Farben zeigen, weil das Frontend seine Startseite zwischenspeichert. Das gilt
auch, wenn du die Datei änderst.

## Datenquelle und Lizenz

Bahnhofs- und Statusdaten stammen von OpenStation der DB InfraGO AG, stehen unter
[CC0](https://creativecommons.org/publicdomain/zero/1.0/) und werden von der
[Mobilithek](https://mobilithek.info/offers/930558234532405248) geladen. Der Code in diesem
Repository steht unter der MIT-Lizenz.

Die durchgestrichenen Icons für Rolltreppen und Fahrsteige sind aus den
[Material Design Icons](https://pictogrammers.com/library/mdi/) abgeleitet (Apache License
2.0).

## Haftungsausschluss

Inoffizielles Community-Projekt, nicht mit der Deutschen Bahn AG oder der DB InfraGO AG
verbunden oder von ihnen unterstützt. Statusdaten können verzögert oder unvollständig sein.
Verlasse dich bei sicherheitsrelevanten Reiseentscheidungen nicht allein auf sie.

## Bekannte Einschränkungen

- Der Status änderte sich bei der Messung unregelmäßig, im Abstand von 50 Sekunden bis 7
  Minuten. Eine Änderung kann also so lange dauern, zuzüglich deines Abfrageintervalls.
- Manche Hauptbahnhöfe haben in der Quelle keine überwachten Anlagen, darunter München Hbf,
  Bochum Hbf und Kassel Hbf. Sie sind in der Bahnhofsliste mit (0) markiert und zeigen statt
  Sensoren einen Hinweis. Andere Halte ohne überwachte Anlagen werden nicht aufgeführt.
- Die Quelle führt nicht jeden Aufzug. Für Frankfurt (Main) Hbf waren es beim Vergleich 2 in
  den Daten, auf bahnhof.de dagegen etwa 10.
- Rund 8 % der Aufzüge haben in der Quelle keine Bahnsteig-Verknüpfung. Ihr Name sagt aber oft,
  wohin sie führen.
- Manche Anlagen haben in der Quelle keinen Namen und werden mit ihrer Nummer angezeigt. Rund
  5 % der Anlagen meldeten bei der Messung `unknown`.
- Ob der Status zum tatsächlichen Zustand der Anlagen passt, wurde nicht geprüft.
- Neu in der Quelle aufgeführte Anlagen eines Bahnhofs erscheinen nach dem nächsten Neuladen
  der Integration.
- Die erste Einrichtung lädt und verarbeitet eine 19 MB große Datei. Auf kleiner Hardware wie
  einem Raspberry Pi wurde das nicht gemessen.

---

# English

An unofficial custom integration that shows whether elevators, escalators and travelators
at German railway stations are working, using DB InfraGO's open
[OpenStation](https://github.com/dbinfrago/openstation-docs) data. Searching for
"OpenStation" finds it in Home Assistant as well.

## What it does and does not do

It adds one device for each station you pick, with one binary sensor for each elevator,
escalator and travelator there. Sensors are named and shown with an icon by type, such as
"Elevator zu Gleis 5/6". Descriptions come from the source in German. Where the source
links an elevator to a platform, the sensor lists that platform.

It does not tell you whether a track is reachable step-free or plan a route, and it does
not cover stations outside DB InfraGO's network.

## Requirements

- Home Assistant 2026.10.4 or newer
- Internet access. The integration needs no account or API key. Only adding it from a link
  in the Marketplace requires a connection to GitHub.
- On Home Assistant 2026.10, also [HACS](https://hacs.xyz/). From 2026.11 on it is built in
  as the Marketplace.

## Installation

### Marketplace (Home Assistant 2026.11 and newer)

1. Open **Settings > Marketplace** and choose **Add from link**. Connect GitHub if asked.
2. Enter `https://github.com/open-data-for-ha/ha-openstation` with the type **Integration**.
3. Install **Öffentliche Bahnhofsdaten** and restart Home Assistant.

If you already installed it through HACS, Home Assistant takes it over when you update to
2026.11.

### HACS (Home Assistant 2026.10)

1. In HACS, open the menu and choose **Custom repositories**.
2. Add `https://github.com/open-data-for-ha/ha-openstation` with the type **Integration**.
3. Install **Öffentliche Bahnhofsdaten** and restart Home Assistant.

### Manual

Copy `custom_components/openstation` into your Home Assistant `custom_components` folder
and restart.

## Configuration

Go to **Settings > Devices & services > Add integration** and search for
**Öffentliche Bahnhofsdaten** or **OpenStation**. Then pick your stations. The first run
downloads the station list, which can take a minute.

The station list shows main stations first, also while you type a city name.

To add or remove a station later, open **Settings > Devices & services > Öffentliche
Bahnhofsdaten** and choose **Configure**. There is no separate add button: all stations
share one entry, so that the source is polled only once. The same dialog sets the polling
interval (60 to 3600 seconds, default 300).

## Entities

| Shown as | State | Meaning |
| --- | --- | --- |
| In service | `off` | Reported as working |
| Out of service | `on` | Reported as out of service |
| Unknown | `unknown` | The source does not know the status |
| Unavailable | `unavailable` | The source lists no status for it, or the feed is over 30 minutes old |

Attributes: `station`, `platforms`, `equipment_number` and `source_status`.

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

### Icons and colors

Icons always show the type of equipment and are crossed out when it is out of service.
Colors come from Home Assistant, which only marks out of service in red. For green when in
service and gray when unknown, add a theme and select it in your user profile:

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

Then load it in `configuration.yaml`:

```yaml
frontend:
  extra_module_url:
    - /local/openstation-colors.js
```

Restart Home Assistant, then clear the browser cache. A normal reload can keep showing
the old colors because the frontend caches its start page. The same applies after
changing the file.

## Data source and license

Station and status data comes from OpenStation by DB InfraGO AG, released under
[CC0](https://creativecommons.org/publicdomain/zero/1.0/) and fetched from
[Mobilithek](https://mobilithek.info/offers/930558234532405248). The code in this
repository is under the MIT license.

The crossed-out escalator and travelator icons are derived from
[Material Design Icons](https://pictogrammers.com/library/mdi/) (Apache License 2.0).

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
