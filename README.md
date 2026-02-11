# Proxmox Mail Gateway (PMG) – Home Assistant Integration

Diese Integration stellt Sensoren für Proxmox Mail Gateway (PMG) bereit und unterstützt das Einrichten über den Config‑Flow. Sie ist für mehrere Geräte/Hosts ausgelegt und funktioniert mit der PMG‑API über `pmgproxy` (Port 8006).

## Features
- Config‑Flow (UI‑Einrichtung)
- Mehrere Geräte/Hosts möglich
- Diagnose‑Daten (Diagnostics)
- Mail‑Statistiken (z. B. Spam, Junk, Bytes, Pregreet, RBL, SPF)
- System‑/Node‑Status (CPU, Load, RAM, Disk, Uptime)
- Update‑Sensor pro Node (Anzahl verfügbarer Updates via `/nodes/{node}/apt/update`)

## Installation (manuell)
1. Ordner `custom_components/pmg` in dein Home‑Assistant‑Config‑Verzeichnis kopieren.
2. Home Assistant vollständig neu starten.
3. Integration hinzufügen: **Einstellungen → Geräte & Dienste → Integration hinzufügen → Proxmox Mail Gateway**

## Installation via HACS (Benutzerdefiniertes Repository)
Du kannst dieses GitHub‑Repository in HACS als **benutzerdefiniertes Repository** hinzufügen und dann die Integration installieren.

Kurzablauf:
1. HACS öffnen → **Integrationen** → Menü → **Benutzerdefinierte Repositories**
2. Repository‑URL hinzufügen: `https://github.com/hannes0217/pmg`
3. Kategorie: **Integration**
4. Danach die Integration installieren und Home Assistant neu starten.

## Konfiguration (Config‑Flow)
- **Host**: IP oder Hostname ohne `https://` (z. B. `192.168.1.229`)
- **Port**: Standard `8006`
- **Benutzername**: z. B. `root`
- **Realm**: z. b. `pam` (oder `pmg` für PMG‑User)
- **Verify SSL**: bei Self‑Signed Zertifikat deaktivieren

## Optionen
- **Verify SSL**: TLS‑Zertifikat prüfen
- **Scan interval**: Abfrageintervall in Sekunden
- **Statistics range**: Zeitraum der Statistiken in Tagen

## Sensoren (Auszug)
### System/Node
- CPU Usage
- Load Average (1m)
- Memory Used/Total
- Disk Used/Total
- Uptime

### Mail‑Statistiken
- Mail Total / In / Out
- Junk / Spam / Virus
- Bytes In / Out
- Bounces In / Out
- Greylist
- Pregreet Rejects
- RBL Rejects
- SPF Rejects
- AVP Time

### Updates
- Updates Available (Anzahl verfügbarer Updates pro Node)

## Hinweise
- Die PMG‑Web‑UI zeigt nicht alle Statistikfelder an. Die Integration nutzt die Rohdaten aus `/statistics/mail`.
- Bei älteren PMG‑Versionen können einzelne Felder fehlen; Sensoren bleiben dann „Unbekannt“.
- Update‑Check nutzt `/nodes/{node}/apt/update`.

## Support
Bitte Issues im GitHub‑Repository erstellen.

---

## Development
Dieses Repository ist ein Home‑Assistant Custom Component‑Projekt. Die Integration befindet sich unter `custom_components/pmg`.
