# 🎯 A-Darts Turnier Manager

Eine moderne, webbasierte Anwendung zur Verwaltung von Darts-Turnieren (oder ähnlichen Sportarten). Entwickelt für lokale Turniere mit Freunden, optimiert für Desktop und Mobile.

## ✨ Features

*   **Turniermodus:** Unterstützung für "Jeder gegen Jeden" (Round Robin).
*   **Spielerverwaltung:** Einfaches Hinzufügen von Spielern, "Bekannte Spieler"-Liste für schnellen Start, und Zufalls-Shuffle für die Reihenfolge.
*   **Match-Übersicht:**
    *   Übersichtliches Karten-Design für alle Paarungen.
    *   **Live-Status:** Anzeige von offenen und beendeten Spielen.
    *   **Parallel-Spiel-Logik:** Interaktive Anzeige, welche Spiele parallel stattfinden können (durch Klick auf ein Spiel).
    *   **Fokus:** Hervorhebung aller Spiele eines Spielers per Hover.
*   **Ergebnisse:**
    *   Eingabe über komfortables modales Fenster.
    *   Korrekturfunktion für bereits eingetragene Ergebnisse.
    *   Hervorhebung des Gewinners.
*   **Tabelle:**
    *   Automatische Live-Tabelle.
    *   Sortierung nach Punkten, Direktem Vergleich (Mini-League Logik), Leg-Differenz und gewonnenen Legs.
    *   Optische Hervorhebung der Top 3 (Gold, Silber, Bronze).
*   **Design:**
    *   Modernes Bootstrap 5 Design.
    *   **Dark Mode Support** (automatisch oder manuell umschaltbar).
    *   Responsive (funktioniert auf Handy, Tablet und PC).

## 🚀 Quickstart

1.  Repository klonen oder herunterladen.
2.  Python-Umgebung einrichten (siehe `INSTALL.md`).
3.  App starten:
    ```bash
    python app.py
    ```
4.  Browser öffnen: `http://127.0.0.1:5123`

## 🛠️ Technologie

*   **Backend:** Python, Flask, SQLAlchemy (SQLite)
*   **Frontend:** HTML5, Jinja2, Bootstrap 5.3, JavaScript
*   **Architektur:** Modularer Aufbau (Models, Routes, Utils)

## 📝 Lizenz

Dieses Projekt ist lizenziert unter speziellen Bedingungen (angelehnt an CC BY-NC).

*   ✅ **Nutzung & Weitergabe:** Frei für alle.
*   🏷️ **Namensnennung:** Erforderlich bei Weitergabe.
*   🚫 **Kommerziell:** Nutzung zu kommerziellen Zwecken ist **nicht gestattet**.

Details siehe [LICENSE](LICENSE).
