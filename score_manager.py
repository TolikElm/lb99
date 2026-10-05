"""
score_manager.py - Verwaltung und dauerhafte Speicherung der Highscores & Statistiken
Speichert Spielergebnisse und Lebenszeit-Statistiken in einer lokalen JSON-Datei.
"""

import os
import json
import tempfile
from datetime import datetime


class ScoreManager:
    DEFAULT_MAX_ENTRIES = 10

    def __init__(self, filename: str = "highscores.json"):
        # Relativ zum Verzeichnis dieser Datei speichern
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.filepath = os.path.join(base_dir, filename)
        self.data = self._get_default_data()
        self.load()

    def _get_default_data(self) -> dict:
        return {
            "all_time_high": 0.0,
            "last_player_name": "PLAYER",
            "lifetime_stats": {
                "games_played": 0,
                "games_won": 0,
                "total_popped": 0,
                "total_clicks": 0,
            },
            "leaderboard": [],
        }

    def load(self):
        """Lädt die Highscore-Daten aus der JSON-Datei. Fällt bei Fehlern sicher auf Defaults zurück."""
        if not os.path.exists(self.filepath):
            self.data = self._get_default_data()
            return

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            defaults = self._get_default_data()
            # Fehlende Schlüssel auffüllen
            for key, val in defaults.items():
                if key not in loaded:
                    loaded[key] = val
            for stat_key, stat_val in defaults["lifetime_stats"].items():
                if stat_key not in loaded.get("lifetime_stats", {}):
                    loaded.setdefault("lifetime_stats", {})[stat_key] = stat_val

            self.data = loaded
        except (json.JSONDecodeError, OSError) as e:
            print(f"[ScoreManager] Warnung beim Laden von {self.filepath}: {e}. Verwende Standardwerte.")
            self.data = self._get_default_data()

    def save(self):
        """Speichert die Daten atomar in die JSON-Datei, um Datenverlust bei Spielabbruch zu verhindern."""
        try:
            base_dir = os.path.dirname(self.filepath)
            # In temporäre Datei schreiben und dann ersetzen (atomar)
            with tempfile.NamedTemporaryFile("w", dir=base_dir, delete=False, encoding="utf-8") as tf:
                json.dump(self.data, tf, indent=2, ensure_ascii=False)
                temp_name = tf.name

            os.replace(temp_name, self.filepath)
        except OSError as e:
            print(f"[ScoreManager] Fehler beim Speichern nach {self.filepath}: {e}")

    def is_high_score(self, score: float, max_entries: int = DEFAULT_MAX_ENTRIES) -> bool:
        """Prüft, ob der gegebene Score für die Bestenliste qualifiziert ist."""
        if score <= 0:
            return False

        leaderboard = self.data.get("leaderboard", [])
        if len(leaderboard) < max_entries:
            return True

        # Schlägt mindestens den letzten Platz
        return score > leaderboard[-1].get("score", 0.0)

    def record_game_finished(self, won: bool, popped: int, clicks: int):
        """Aktualisiert die Gesamtstatistiken (gespielte Runden, Siege, Ballons)."""
        stats = self.data.setdefault("lifetime_stats", {})
        stats["games_played"] = stats.get("games_played", 0) + 1
        if won:
            stats["games_won"] = stats.get("games_won", 0) + 1
        stats["total_popped"] = stats.get("total_popped", 0) + popped
        stats["total_clicks"] = stats.get("total_clicks", 0) + clicks
        self.save()

    def add_score(
        self,
        name: str,
        score: float,
        popped: int,
        accuracy_pct: float,
        won: bool,
        clicks: int,
        max_entries: int = DEFAULT_MAX_ENTRIES,
    ) -> int:
        """
        Fügt ein neues Ergebnis hinzu, sortiert die Bestenliste und speichert.
        Gibt die erreichte Platzierung (1-basiert) zurück, oder -1 falls nicht in Top 10.
        """
        clean_name = (name.strip().upper() or "PLAYER")[:12]
        self.data["last_player_name"] = clean_name

        entry = {
            "name": clean_name,
            "score": round(score, 1),
            "balloons_popped": popped,
            "accuracy_pct": round(accuracy_pct, 1),
            "won": won,
            "clicks": clicks,
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        }

        leaderboard = self.data.setdefault("leaderboard", [])
        leaderboard.append(entry)

        # Sortieren: Primär nach Score (absteigend), sekundär nach Genauigkeit (absteigend)
        leaderboard.sort(key=lambda x: (x.get("score", 0.0), x.get("accuracy_pct", 0.0)), reverse=True)

        # Rang ermitteln
        rank = -1
        try:
            rank = leaderboard.index(entry) + 1
        except ValueError:
            pass

        # Auf max_entries beschränken
        self.data["leaderboard"] = leaderboard[:max_entries]

        # All-time High aktualisieren
        current_high = self.data.get("all_time_high", 0.0)
        if score > current_high:
            self.data["all_time_high"] = round(score, 1)

        self.save()

        # Prüfen, ob Eintrag noch in den Top entries ist
        if rank <= max_entries:
            return rank
        return -1

    def get_leaderboard(self) -> list[dict]:
        """Gibt die sortierte Bestenliste zurück."""
        return self.data.get("leaderboard", [])

    def get_all_time_high(self) -> float:
        """Gibt den Allzeit-Punkterekord zurück."""
        return self.data.get("all_time_high", 0.0)

    def get_last_player_name(self) -> str:
        """Gibt den zuletzt verwendeten Spielernamen zurück."""
        return self.data.get("last_player_name", "PLAYER")

    def get_lifetime_stats(self) -> dict:
        """Gibt die Gesamtstatistiken zurück."""
        return self.data.get("lifetime_stats", {})
