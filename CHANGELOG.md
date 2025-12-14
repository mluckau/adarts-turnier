# 📝 Changelog

Alle Änderungen am A-Darts Turnier Manager werden hier dokumentiert.

## [Unreleased] - 2025-12-14

### Hinzugefügt
*   **Projektstruktur:** Refactoring in `app.py` (Entrypoint), `models.py` (Datenbank), `routes.py` (Logik) und `utils.py` (Helper).
*   **Sortierlogik:** Implementierung einer "Mini-League"-Logik für faire Tabellenberechnung bei Punktgleichheit (Direkter Vergleich auch bei >2 Spielern).
*   **Turniermodi:** Vorbereitung der Datenbank für verschiedene Modi (Feld `mode` im Tournament Model).
*   **UI/UX Improvements:**
    *   **Shuffle-Button:** Zufälliges Mischen der Spielernamen vor Turnierstart.
    *   **Automatisches Datum:** Turniername wird mit aktuellem Datum vorausgefüllt.
    *   **Duplikat-Schutz:** Automatische Nummerierung bei doppelten Turniernamen.
    *   **Layout:** Grid-Ansicht für Matches (2 Spalten auf Desktop).
    *   **Ergebnis-Eingabe:** Modales Fenster für Scores, Standardwert '0', keine negativen Zahlen.
    *   **Visualisierung:** Medaillen (Gold, Silber, Bronze) und farbige Hintergründe in der Tabelle.
    *   **Interaktion:** Klick auf Match-Karte zeigt parallel spielbare Matches an (Grün).

### Geändert
*   **Architektur:** Umstellung von einer monolithischen `app.py` auf Blueprints.
*   **Port:** Standard-Port von 5000 auf **5123** geändert.
*   **Design:** Umstellung von Listen-Ansicht auf **Match-Cards** mit Avataren.
*   **Dark Mode:** Vollständige Unterstützung und Toggle-Button in der Navbar.

### Behoben
*   Fix: `url_for` Aufrufe nach Blueprint-Umstellung korrigiert.
*   Fix: Template-Syntaxfehler durch falsche Block-Verschachtelung.
*   Fix: JavaScript-Logik für Score-Modal (leerte Felder bei neuen Matches).
*   Fix: Grid-Layout-Bugs bei ungerader Anzahl von Matches pro Runde.

---

## [Initial] - Prototyp

*   Basis-Funktionalität: Spieler hinzufügen, Round-Robin-Plan generieren, Ergebnisse eintragen.
*   Einfache Tabelle nach Punkten.
*   SQLite Datenbankanbindung.
