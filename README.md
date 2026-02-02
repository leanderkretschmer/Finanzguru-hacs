# Finanzguru (Home Assistant Custom Component)

![Finanzguru Logo](custom_components/finanzguru/logo.svg)

Diese Integration verbindet Home Assistant mit Finanzguru und stellt Kennzahlen als Sensoren bereit (z. B. monatliche Ausgaben/Einnahmen, heutige Ausgaben, Verträge, Budgets).

Da Finanzguru keine öffentliche API-Dokumentation für Drittanbieter bereitstellt, verwendet diese Integration einen Login-Flow mit Token-Handling (Access/Refresh-Token) und aktualisiert Tokens automatisch, damit du dich nicht ständig neu anmelden musst.

## Features

- Config Flow (UI-Setup) über E-Mail/Passwort (Passwort wird nicht gespeichert)
- Zentraler Datenabruf über DataUpdateCoordinator (Standard: alle 30 Minuten)
- Sensoren:
  - Monatliche Ausgaben (inkl. Kategorien in Attributen)
  - Monatliche Einnahmen (inkl. Kategorien in Attributen)
  - Heutige Ausgaben
  - Verträge (State: Anzahl, Attribute: Liste mit Name/Preis/Zahlungsrate)
  - Budget-Auslastung (optional, je nach gelieferten Daten)

## Installation (HACS)

1. HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories
2. Repository-URL eintragen (GitHub-URL) und Typ auf Integration setzen
3. In HACS nach „Finanzguru“ suchen und installieren
4. Home Assistant neu starten
5. Einstellungen → Geräte & Dienste → Integration hinzufügen → „Finanzguru“

## Installation (Manuell)

1. Den Ordner [custom_components/finanzguru](file:///c:/Users/leander/Projekte/hacs-finanzguru/custom_components/finanzguru) nach `/config/custom_components/finanzguru` kopieren
2. Home Assistant neu starten
3. Einstellungen → Geräte & Dienste → Integration hinzufügen → „Finanzguru“

## Konfiguration

- Die Konfiguration erfolgt vollständig über den UI-Dialog.
- Beim Setup werden Access-/Refresh-Token in der Config-Entry-Data gespeichert; beim Aktualisieren der Daten werden Tokens bei Bedarf automatisch erneuert.

## Lovelace Karten (Presets)

Nach der Installation und dem Hinzufügen der Integration erscheinen Finanzguru-Karten unter „Zum Dashboard hinzufügen“ → „Benutzerdefinierte Karten“ als auswählbare Presets:

- Finanzguru: Monat
- Finanzguru: Heute
- Finanzguru: Verträge
- Finanzguru: Budget

## Troubleshooting

- Wenn nach Updates die Karten nicht erscheinen: Browser Cache leeren und/oder Frontend neu laden.
- Wenn die Anmeldung fehlschlägt: Integration in Geräte & Dienste neu konfigurieren (Reauth).
