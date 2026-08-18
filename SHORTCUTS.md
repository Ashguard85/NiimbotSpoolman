# Schnellzugriffe

## Direkter Spool-Link

Die App akzeptiert:

```text
https://labels.meineURL.com/#spool=123
```

oder als Pages-URL:

```text
https://USER.github.io/REPO/#spool=123
```

Zusätzlich werden als `url=` oder `text=` übergebene Spoolman-Werte erkannt:

```text
web+spoolman:s-123
https://spoolman.meineURL.com/spool/show/123
```

## Android Share Target

Wenn die PWA auf dem Lenovo installiert ist, registriert sie sich als Share Target. Teile aus Chrome die aktuelle Spoolman-Rollenseite an „Spool Labels“. Die App liest die Spool-ID aus der URL und öffnet direkt die Rolle.

## Externe Integration

Andere Dienste können direkt `#spool=<id>` aufrufen. Damit lässt sich später auch ein Button in einem Dashboard, Home Assistant, Moonraker oder einem eigenen Spoolman-Frontend ergänzen, ohne PDF-Erzeugung.
