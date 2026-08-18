# Release v6
- Eigenständiger Spoolman→NIIMBOT-Dienst
- Android-/Tablet-first UI
- dynamische Nutzung aller Spoolman-Spool-/Filament-/Vendor-/Extra-Felder
- Vorlagen mit Platzhaltern und Feldbrowser
- Formate 40×40, 50×30, 30×20, 50×50
- direkte B1-Ausgabe über Web Bluetooth
- Spoolman-URL, web+spoolman-Code oder Spool-ID als QR
- Android Web Share Target
- Local-/Server-Modus
- Docker-Spoolman-Proxy, SQLite Templates/History, Backup/Restore

## Dynamische Etiketten

- Beliebig viele Textzeilen statt fest drei Zeilen.
- Leere Spoolman-Felder blenden die betroffene Zeile automatisch aus.
- Automatische Schriftgröße und vertikale Verteilung anhand der tatsächlich sichtbaren Zeilen.
- Layoutwahl: Automatisch, QR links oder QR oben.
- Neue 50×30-Vorlage „Spoolman dynamisch“ im Stil QR links / Daten rechts.
- Alte v1-Vorlagen und v1-Backups bleiben importierbar.

- 50×30-Querformat: QR links nutzt jetzt nahezu die volle nutzbare Labelhöhe; Text rechts skaliert dynamisch in der Restbreite.

- Neue QR-Größe-Auswahl in der UI: ausgewogen, QR groß, QR sehr groß, automatisch.

- Neuer QR-Breiten-Slider in % sowie Text-Ausrichtung oben/mittig/unten.
- Automatische QR-Größe und Text-Ausrichtung berücksichtigen jetzt die tatsächliche Zeilenzahl.

- QR-Renderer korrigiert: der bisher intern fest reservierte 4-Modul-Rand ist jetzt einstellbar (0/1/2/4).
- 50×30 Seitenlayout nutzt nur noch 2 px äußeren QR-Abstand und kann die volle Labelhöhe besser ausnutzen.
- QR-ECC L/M/Q/H konfigurierbar; dynamische 50×30-Vorlage nutzt standardmäßig ECC L + 1 Modul Rand für größere Druckmodule.
- Optionaler QuickChart-QR-Renderer mit automatischem lokalem Fallback.
- Renderstatus zeigt jetzt QR-Feld- und tatsächliche Code-Pixelgröße.
