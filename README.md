# 🎈 99-Luftballons

Ein rasantes 2D-Arcade- und Aim-Trainer-Geschicklichkeitsspiel in Python mit **Pygame**.

Steigen lassen war gestern – jetzt heißt es zielen! Genau 99 Luftballons steigen von unten auf. Deine Mission: Bringe alle Ballons zum Platzen, bevor auch nur ein einziger den oberen Bildschirmrand erreicht.

---

## 🎮 Gameplay & Spielmechanik

### 🎯 Kernziel: Sudden Death & Sieg
* **Sudden Death:** Berührt ein einziger Ballon mit seiner Oberkante die obere Leiste ($y - r \le 0$), ist das Spiel **sofort vorbei** (Game Over).
* **Sieg:** Zerplatze alle 99 Luftballons, um das Spiel erfolgreich abzuschließen.

---

### 🎈 Ballongrößen & Punktesystem
Es existieren 5 verschiedene Größenstufen. Kleinere Ballons steigen etwas schneller auf, sind schwerer zu treffen und bringen die meisten Punkte:

| Stufe | Durchmesser | Pixel-Ø | Radius | Basispunkte | Farbe |
| :---: | :---------: | :-----: | :----: | :---------: | :---: |
| **1** | 1,00 cm     | 40 px   | 20 px  | **5 Pkt.**  | Rot |
| **2** | 1,25 cm     | 50 px   | 25 px  | **4 Pkt.**  | Orange |
| **3** | 1,50 cm     | 60 px   | 30 px  | **3 Pkt.**  | Gelb |
| **4** | 1,75 cm     | 70 px   | 35 px  | **2 Pkt.**  | Grün |
| **5** | 2,00 cm     | 80 px   | 40 px  | **1 Pkt.**  | Blau |

---

### ⏱️ Die 50%-Auftauchregel & Transparenz
* Ballons starten außerhalb des unteren Bildschirmrands.
* **Dynamisches Einblenden:** Beim Eintritt durch die Unterkante ist der Ballon anfangs transparent (Alpha-Wert ca. 70) und gewinnt mit dem Aufsteigen an voller Farbintensität (Alpha 255).
* **Klick-Erlaubnis:** Ein Ballon darf **erst dann angeklickt werden**, wenn **mehr als die Hälfte** des Kreises sichtbar ist ($y_{\text{Mitte}} < \text{screen\_height}$). Klicks auf gerade erst angeschnittene Ballons zählen nicht.

---

### 🎯 Präzisionswertung (Treffgenauigkeit)
Treffer werden nach Genauigkeit bewertet – je näher der Klick am Mittelpunkt des Ballons liegt, desto höher die Ausbeute:
* **Exakte Mitte ($d = 0$):** 100% der Basispunkte (Bullseye / Perfekt!)
* **Äußerer Rand ($d = r$):** 10% der Basispunkte
* **Berechnungsformel:**
  $$\text{Genauigkeit} = 1.0 - 0.9 \cdot \left(\frac{d}{r}\right)$$
  $$\text{Punkte} = \text{round}(\text{Basispunkte} \cdot \text{Genauigkeit}, 1)$$

---

### 📈 Dynamische Schwierigkeit
* **Aufstiegsbewegung:** Natürlicher Wind-Effekt durch sanftes Schaukeln (Sinus-Wobble).
* **Spawn-Rate:** Zu Beginn startet der Spawner mit 1,6 Sekunden Intervall. Je weiter das Spiel voranschreitet, desto schneller folgen die Ballons aufeinander (bis zu 0,75 Sekunden).
* **Gefahren-Warnleiste:** Nähert sich ein Ballon der oberen Gefahrenzone, glimmt am oberen Rand eine rote Warnleiste auf.

---

### 🔊 Prozedurale Soundeffekte
* Das Spiel benötigt **keine externen Audio-Dateien** (`.wav`, `.mp3`).
* Alle Soundeffekte (Plopp-Töne mit tonaler Abstufung je nach Ballongröße, Game-Over- und Sieges-Jingle) werden in Echtzeit als PCM-Wellenformen prozedural im Speicher synthetisiert.

---

## 🕹️ Steuerung

| Eingabe | Aktion |
| :--- | :--- |
| **Linke Maustaste (LMB)** | Ballon anvisieren und zerplatzen / Starten / Neustart |
| **Taste `R`** | Laufendes Spiel neustarten / Reset |
| **Taste `ESC`** | Spiel beenden |

---

## 🚀 Installation & Start

### Voraussetzungen
* Python 3.9 oder höher
* Paketmanager `pip`

### 1. Repository klonen oder herunterladen
```bash
cd LB99
```

### 2. Virtuelle Umgebung erstellen (empfohlen)
```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

### 4. Spiel starten
```bash
python main.py
```

---

## 📂 Projektstruktur

```text
LB99/
├── PLAN.md              # Ursprüngliches Konzept & Spezifikationsplan
├── README.md            # Projektdokumentation & Anleitung
├── requirements.txt     # Python-Abhängigkeiten (pygame)
├── main.py              # Hauptspielschleife, State-Management & HUD
├── balloon.py           # Ballon-Klasse (Physik, 50%-Regel, Alpha-Fading, Klickprüfung)
├── effects.py           # Visuelle Partikeleffekte & schwebende Punkteanzeigen
└── sound.py             # Prozeduraler Sound-Synthesizer via pygame.mixer
```

---

## 📊 Spielendstände & Statistiken

Nach Rundenende (Sieg oder Sudden Death) erhältst du eine Zusammenfassung mit:
* Erreichten Gesamtpunkten
* Anzahl der zerplatzten Ballons
* Durchschnittlicher Treffgenauigkeit in Prozent
* Gesamtzahl der Klicks
