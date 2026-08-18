# Spoolman NIIMBOT Labels – Docker v1

Vollständige Fullstack-Version des Spoolman-Label-Dienstes. Enthält Flask-Backend, SQLite, Spoolman-Proxy, Templates, Druckverlauf, Backup/Restore, PWA-Frontend und alle statischen Assets.

## Ziel

Spoolman auswählen → Label rendern → direkt aus Android/Chrome per Web Bluetooth auf NIIMBOT B1 drucken. Kein PDF-Export aus Spoolman und kein Import in die NIIMBOT-App.

## Docker / Portainer

Die App läuft in `/app`; persistente Daten liegen ausschließlich in `/app/data`.

```yaml
services:
  spoolman-niimbot:
    build:
      context: https://github.com/USER/spoolman-niimbot.git#main
    ports:
      - "8090:8080"
    volumes:
      - /home/USER/docker/spoolman-niimbot/data:/app/data
    environment:
      - APP_URL=https://labels.meineURL.com
      - SPOOLMAN_URL=http://spoolman:8000
      - SPOOLMAN_PUBLIC_URL=https://spoolman.meineURL.com
      - PWA_ALLOWED_ORIGIN=https://USER.github.io
      - BACKUP_KEEP=50
    restart: unless-stopped
```

## Environment

- `APP_URL`: öffentliche Label-App-URL
- `SPOOLMAN_URL`: vom Container erreichbare Spoolman-Basis-URL; darf intern/LAN sein
- `SPOOLMAN_PUBLIC_URL`: URL, die in QR-Codes landen soll
- `PWA_ALLOWED_ORIGIN`: exakt erlaubte externe Pages-Origin
- `BACKUP_KEEP`: Anzahl SQLite-Sicherungen
- `SPOOLMAN_TIMEOUT`: Proxy-Timeout in Sekunden
- `SPOOLMAN_CF_CLIENT_ID` / `SPOOLMAN_CF_CLIENT_SECRET`: optionaler serverseitiger Cloudflare-Service-Token, falls Spoolman selbst hinter Access liegt; wird nie ans Frontend ausgegeben

## API

- `GET /health`
- `GET /api/config`
- `GET /api/spoolman/<path>` – GET-only Proxy zur fest konfigurierten Spoolman-API
- `GET|POST /api/templates`
- `DELETE /api/templates/<id>`
- `GET|POST|DELETE /api/history`
- `GET /api/export`
- `POST /api/import`

Der Proxy akzeptiert keine frei vom Browser angegebene Ziel-URL; damit wird kein generischer SSRF-Proxy bereitgestellt.

## SQLite

`/app/data/app.sqlite`, WAL, `synchronous=FULL`, `foreign_keys=ON`. Vor Restore wird ein SQLite-Backup unter `/app/data/backups/` erstellt.

## Spoolman-Daten und Vorlagen

Das Frontend nutzt die vollständige verschachtelte Spool-Antwort. Alle `spool.*`, `filament.*`, `vendor.*` und `extra.*`-Felder werden dynamisch als Platzhalter angeboten. Damit bleibt die App kompatibel mit individuellen Extra-Feldern.

## Cloudflare

Das Docker-Frontend kann normal über Cloudflare Access/OTP geschützt werden. Für die externe Pages-PWA kann ein eigener Service Token verwendet werden. `PWA_ALLOWED_ORIGIN` schränkt CORS ein; `CF-Access-Client-Id` und `CF-Access-Client-Secret` sind als Preflight-Headers zugelassen.

## Pages-Kompatibilität

Docker v1 ↔ Pages v1. Das Frontend ist bis auf `config.js` identisch: Docker startet standardmäßig im Server-Modus, Pages im lokalen Modus.

## Backup / Restore

JSON-Format `spoolman-niimbot-backup`, Version 1. Server-Backups enthalten Templates und Verlauf; Spoolman selbst bleibt die führende Quelle für Spool-/Filament-/Vendor-Daten.

## Bekannte Grenzen

- Hardwaredruck muss auf echtem B1 getestet werden.
- 40×40, 30×20 und 50×50 sind geometrisch abgeleitet; 50×30 nutzt die bekannte B1-Geometrie 384×240.
- QR-/NIIMBOT-Browserbibliotheken werden in v1 von UNPKG geladen und anschließend vom Service Worker gecacht.

## Direkte Aufrufe

`/#spool=<id>` öffnet eine Rolle direkt. Die installierte Android-PWA kann außerdem als Share Target eine Spoolman-URL aus Chrome übernehmen.
