# 📦 Installationsanleitung

Diese Anleitung beschreibt, wie du den A-Darts Turnier Manager auf deinem System installierst und ausführst.

## Voraussetzungen

*   **Python 3.8** oder neuer installiert.
*   Einen Webbrowser.

## Schritt 1: Projekt herunterladen

Lade den Ordner mit den Programmdateien herunter und entpacke ihn (oder klone das Repository).
Öffne ein Terminal (Eingabeaufforderung) und navigiere in diesen Ordner:

```bash
cd /pfad/zu/adarts-turnier
```

## Schritt 2: Virtuelle Umgebung erstellen (Empfohlen)

Es ist Best Practice, eine virtuelle Umgebung zu nutzen, um die Abhängigkeiten isoliert zu halten.

**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

## Schritt 3: Abhängigkeiten installieren

Installiere alle benötigten Python-Pakete automatisch mit `pip`:

```bash
pip install -r requirements.txt
```

## Schritt 4: Anwendung starten

Starte den Server mit folgendem Befehl:

```bash
python app.py
```

Du solltest eine Ausgabe sehen, die bestätigt, dass der Server läuft (normalerweise auf Port 5123).

## Schritt 5: Öffnen

Öffne deinen Webbrowser und gehe zu:

[http://127.0.0.1:5123](http://127.0.0.1:5123)

Viel Spaß beim Turnier! 🎯
