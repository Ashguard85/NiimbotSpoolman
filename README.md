# Spoolman NIIMBOT Labels – Pages v8

Statische, Android-/Tablet-first PWA zum direkten Drucken von Spoolman-Spooldaten auf einem NIIMBOT B1. Kein PDF-Zwischenschritt: Spoolman-Daten → Canvas → Web Bluetooth → B1.

## Architektur

- Gemeinsames Frontend mit Docker v8.
- Pages enthält kein Python, SQLite oder Server-Secrets.
- Lokaler Modus: Browser spricht per HTTPS/CORS direkt mit Spoolman.
- Server-Modus: Browser spricht mit dem Docker-Backend; dieses proxyt ausschließlich zur fest konfigurierten Spoolman-Instanz.
- Druck läuft immer direkt vom Endgerät über Web Bluetooth zum B1.
- Primärziel: Lenovo/Android 14 + Chrome. iPhone/Bluefy bleibt als experimenteller BLE-Weg möglich.

## Spoolman-Daten

Die App ist absichtlich schemaflexibel. Sie flacht die komplette Antwort eines Spools ab:

- `spool.*` – alle Spool-Felder
- `filament.*` – alle Felder des verschachtelten Filaments
- `vendor.*` – alle Felder des verschachtelten Vendors
- `*.extra.*` – sämtliche benutzerdefinierten Extra-Felder werden automatisch sichtbar
- abgeleitet: `spool.url`, `spool.scheme`, `spool.remaining_percent`

Dadurch können neue oder eigene Spoolman-Felder ohne Codeänderung in Vorlagen verwendet werden.

Beispiele:

```text
{{spool.id}}
{{spool.location}}
{{spool.remaining_weight|g}}
{{spool.remaining_percent|pct}}
{{filament.material}}
{{filament.name}}
{{filament.color_hex}}
{{vendor.name}}
{{spool.extra.meinfeld}}
```

Filter: `|g`, `|kg`, `|pct`, `|date`.

## Label-Formate

v8 enthält 40×40 mm (Standard), 50×30 mm, 30×20 mm und 50×50 mm. Die 50-mm-Breite wird beim B1 auf 384 Druckpixel begrenzt. Nicht jede Rolle/Gap-Geometrie ist hardwarekalibriert; Offset-/Formatfeintuning sollte mit der echten Rolle geprüft werden.

## QR-Inhalte

- Öffentliche Spoolman-URL `/spool/show/<id>`
- `web+spoolman:s-<id>`
- nur Spool-ID
- eigene Template-Zeichenfolge

## Lenovo / Android 14

1. Seite in Chrome öffnen.
2. Optional als PWA installieren.
3. In Setup Spoolman-Modus konfigurieren.
4. `B1 verbinden` drücken und Drucker wählen.
5. Spool auswählen und `Drucken` oder `Schnelldruck` nutzen.

Das Manifest enthält ein Web Share Target. Wenn die PWA installiert ist, kann eine geteilte Spoolman-URL an die Label-App übergeben werden; die App erkennt `/spool/show/<id>` sowie `web+spoolman:s-<id>`.

## Lokaler Modus

Direkter API-Aufruf zu `https://spoolman.example/.../api/v8`. Spoolman muss HTTPS und CORS für die Pages-Origin erlauben. Eine HTTPS-PWA kann keine unsichere `http://`-Spoolman-Instanz als Mixed Content abrufen.

## Server-Modus

Pages → HTTPS Docker-Backend → konfigurierte Spoolman-Instanz. Damit kann Spoolman intern im LAN bleiben und muss kein CORS für GitHub Pages liefern. Cloudflare Access Service Token kann im Pages-Setup lokal gespeichert werden; Tokens landen nicht in Backup-Exports.

## Offline

App-Shell und geladene CDN-Bibliotheken werden vom Service Worker gecacht. In v8 werden aktuelle Spoolman-Inventardaten nicht als echte Offline-Synchronisation geführt; ohne Spoolman-Verbindung sind daher keine veralteten Daten als aktuell dargestellt.

## Backup

Lokaler Modus: JSON-Backup mit Format `spoolman-niimbot-backup`, Version 2. Enthält lokale Vorlagen, Verlauf und nicht geheime Einstellungen. Cloudflare Client Secret wird nicht exportiert.

## GitHub Pages

Einmalig `Settings → Pages → Build and deployment → Source: GitHub Actions` setzen. Danach deployt der Workflow automatisch. Der ZIP-Importer schützt den kompletten Ordner `.github/workflows/`.

## Update-Lifecycle

Service-Worker-Cache: `spoolman-niimbot-v8`. Neue Releases erhöhen die Cache-Version. Es gibt keine automatische `controllerchange → location.reload()`-Schleife.

## Bekannte Grenzen v8

- Reale B1-Label-/Gap-Kalibrierung muss mit deiner Rolle getestet werden.
- BLE-Druck kann in dieser Umgebung nicht mit echter Hardware getestet werden.
- Die QR- und NIIMBOT-JavaScript-Bibliotheken werden beim ersten Online-Start über UNPKG geladen und danach gecacht; für eine spätere Produktionsversion sollten sie vendort werden.
- Share Target ist für Android/Chromium gedacht; Browser-/OS-Unterstützung kann variieren.

## Direkte Aufrufe

Siehe `SHORTCUTS.md`. Besonders für Android ist `#spool=<id>` und das installierte Web Share Target vorgesehen.

## QR-Druckqualität

Für 50×30 nutzt die Standardvorlage in v8 einen kompakten QR-Rand von 1 Modul und ECC L. Das vergrößert die tatsächlich gedruckten QR-Module. Optional kann der QR mit der QuickChart API gerendert werden; bei Fehlern fällt die App automatisch auf den lokalen Renderer zurück.
