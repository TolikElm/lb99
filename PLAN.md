# Projektplan: 99-Luftballons 🎈

Ein 2D-Arcade-Geschicklichkeitsspiel in Python (Pygame).

---

## 1. Spielkonzept & Übersicht

- **Titel:** 99-Luftballons
- **Genre:** Arcade / Aim Trainer / Balloon Pop
- **Plattform:** Desktop (Python / Pygame)
- **Kernziel:** Es steigen insgesamt genau 99 Luftballons auf. Der Spieler muss diese anklicken und zum Platzen bringen, bevor auch nur ein einziger Ballon die obere Bildschirmkante erreicht.

---

## 2. Spielmechanik im Detail

### 2.1 Ballons & Größenstufen
Es gibt 5 festgelegte Größenstufen. Kleinere Ballons sind schwieriger zu treffen und bringen mehr Punkte:

| Stufe | Durchmesser (cm) | Durchmesser (Pixel)* | Radius (px) | Basispunkte |
| :---: | :--------------: | :------------------: | :---------: | :---------: |
| 1     | 1,00 cm          | 40 px                | 20 px       | **5**       |
| 2     | 1,25 cm          | 50 px                | 25 px       | **4**       |
| 3     | 1,50 cm          | 60 px                | 30 px       | **3**       |
| 4     | 1,75 cm          | 70 px                | 35 px       | **2**       |
| 5     | 2,00 cm          | 80 px                | 40 px       | **1**       |

*\*Richtwert bei Standard-DPI (ca. 96-100 DPI). Entspricht ca. 40 Pixel pro Zentimeter.*

### 2.2 Auftauchen & Sichtbarkeits-Regel (50%-Regel)
- Ballons starten unterhalb des sichtbaren unteren Bildschirmrandes ($y > \text{screen\_height}$).
- **Transparenz / Intensität:** Während des Aufsteigens durch die untere Kante ist der Ballon anfangs blass/transparent (Alpha-Wert gering). Er gewinnt an Farbintensität, je weiter er auf den Bildschirm wandert.
- **Klick-Erlaubnis:** Ein Ballon darf **erst angeklickt werden**, wenn **mehr als die Hälfte** des Kreises sichtbar ist (d. h. der Kreismittelpunkt hat die Bildschirmunterkante überschritten: $y_{\text{center}} \le \text{screen\_height}$).

### 2.3 Präzisionswertung (Treffer-Genauigkeit)
Die tatsächlich vergebenen Punkte hängen davon ab, wie nah am Kreismittelpunkt geklickt wurde:
- **Exakte Mitte ($d = 0$):** 100% der Basispunkte.
- **Äußerer Rand ($d = r$):** 10% der Basispunkte.
- **Formel:**
  $$\text{Genauigkeit} = 1.0 - 0.9 \cdot \left( \frac{d}{r} \right)$$
  $$\text{Punkte} = \text{round}(\text{Basispunkte} \cdot \text{Genauigkeit}, 1)$$
  *(Beispiel: Trifft man Stufe 1 [5 Punkte] mit 80% Genauigkeit, erhält man 4.0 Punkte).*

### 2.4 Spielende & Siegbedingungen
1. **Sudden Death (Game Over):** Erreicht ein nicht-zerplatzter Ballon mit seiner Oberkante ($y - r \le 0$) die oberste Bildschirmkante, ist das Spiel sofort vorbei.
2. **Sieg (Gewonnen):** Alle 99 Luftballons wurden erfolgreich zerplatzt.

---

## 3. Visuelles Design & Audio

1. **Grafik:**
   - Sanftes, leichtes Schwingen der Ballons nach links/rechts (natürlicher Wind/Auftrieb).
   - Ballonglanzpunkt & Bändchen für charmanten Look.
   - Partikeleffekt beim Platzen (kleine Farbspritzer / Konfetti).
   - Floating-Text an der Trefferposition mit erzielter Punktzahl und Trefferqualität (z. B. `+5.0 Bullseye!` oder `+1.8`).
2. **HUD (Heads-Up-Display):**
   - Oben links: Aktueller Gesamtspielstand.
   - Oben rechts: Ballon-Zähler (`Ballon: X / 99`).
   - Oben mittig: Warnanzeige bei Ballons, die sich der Oberkante nähern.
3. **Sound:**
   - Prozedural generierte Soundeffekte über Pygame (hoher Klick/Plopp für kleine Ballons, tieferer Ton für große Ballons). Keine externen WAV/MP3-Dateien nötig!
4. **Endbildschirm (Game Over / Sieg):**
   - Erzielte Gesamtsumme.
   - Anzahl geplatzter Ballons.
   - Durchschnittliche Trefferpräzision in %.
   - Neustart-Option mit Taste `R` oder Klick.

---

## 4. Technische Architektur

- **Programmiersprache:** Python 3
- **Framework:** Pygame
- **Dateistruktur:**
  ```text
  LB99/
  ├── PLAN.md              # Dieser Projektplan
  ├── main.py              # Hauptspielschleife & Spielsteuerung
  ├── balloon.py           # Ballon-Klasse (Physik, Zeichnen, 50%-Logik, Alpha)
  ├── effects.py           # Partikel & aufsteigende Punkte-Texte
  ├── sound.py             # Prozedurale Soundgenerierung
  └── requirements.txt     # Abhängigkeiten (pygame)
  ```

---

## 5. Implementierungs-Schritte

1. [ ] **Schritt 1:** Grundgerüst & Fenstererstellung mit Pygame (`main.py`).
2. [ ] **Schritt 2:** Ballon-Modell (`balloon.py`) mit 5 Größen, Einblenden von unten, 50%-Klick-Logik und Aufstiegsbewegung.
3. [ ] **Schritt 3:** Maus-Klick-Erkennung, Abstands- & Präzisionsberechnung (100% bis 10%).
4. [ ] **Schritt 4:** Partikeleffekte & schwebende Punkteanzeigen (`effects.py`).
5. [ ] **Schritt 5:** Prozedurale Soundeffekte (`sound.py`).
6. [ ] **Schritt 6:** HUD, Spawner (genau 99 Ballons), Spielende-Zustände (Game Over & Sieg).
7. [ ] **Schritt 7:** Feinschliff, Balancing (Aufstiegsgeschwindigkeit, Spawn-Abstände) & Test.
