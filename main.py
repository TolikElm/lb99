"""
main.py - 99-Luftballons Hauptprogramm
Ein Geschicklichkeitsspiel in Pygame mit Highscore-Persistenz & Leaderboard.
"""

import sys
import time
import math
import random
import pygame

from balloon import Balloon, BALLOON_SPECS
from effects import Particle, FloatingText
from sound import SoundManager
from score_manager import ScoreManager

# Fenster-Dimensionen
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60

# Farbdefinitionen (Elegantes Dunkelblau-Theme)
BG_COLOR = (16, 28, 56)              # Sattes Dunkelblau / Mitternachtsblau (statt Schwarz)
TOP_BAR_COLOR = (10, 18, 38)         # Tiefes Dunkelblau für Statusleiste
CARD_BG = (24, 40, 76)               # Dunkelblaue Infoboxen
CARD_BORDER = (45, 72, 130)          # Dezente blaue Kontur / Trennlinien
INPUT_BG = (30, 52, 98)              # Blaues Textfeld für Namenseingabe
OVERLAY_COLOR = (8, 16, 36, 225)     # Dunkelblauer Schleier bei Spielende
WHITE = (250, 250, 250)
GRAY = (150, 165, 195)
GOLD = (255, 215, 0)
RED = (240, 60, 60)
GREEN = (60, 220, 120)
BLUE = (80, 160, 255)
SILVER = (195, 205, 220)
BRONZE = (215, 140, 75)

# Spielzustände
STATE_START = "START"
STATE_PLAYING = "PLAYING"
STATE_NAME_INPUT = "NAME_INPUT"
STATE_GAMEOVER = "GAMEOVER"
STATE_WON = "WON"
STATE_LEADERBOARD = "LEADERBOARD"

TOTAL_BALLOONS = 99


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("99-Luftballons 🎈")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        # Schriftarten laden (Fallback auf Standardschrift)
        self.font_title = pygame.font.SysFont("Helvetica", 44, bold=True)
        self.font_heading = pygame.font.SysFont("Helvetica", 26, bold=True)
        self.font_main = pygame.font.SysFont("Helvetica", 20)
        self.font_small = pygame.font.SysFont("Helvetica", 15)
        self.font_hud = pygame.font.SysFont("Helvetica", 22, bold=True)
        self.font_mono = pygame.font.SysFont("Courier", 17, bold=True)

        self.sounds = SoundManager()
        self.score_manager = ScoreManager()

        self.state = STATE_START

        # Spielvariablen
        self.balloons: list[Balloon] = []
        self.particles: list[Particle] = []
        self.floating_texts: list[FloatingText] = []

        self.score = 0.0
        self.balloons_spawned = 0
        self.balloons_popped = 0
        self.total_clicks = 0
        self.accuracy_sum = 0.0

        self.spawn_timer = 0.0
        self.current_spawn_interval = 1.6
        self.escaped_balloon = None

        # Namenseingabe & Highscore
        self.player_input_name = self.score_manager.get_last_player_name()
        self.last_saved_rank = -1
        self.end_game_reason = ""
        self.is_victory = False

    def reset_game(self):
        """Setzt alle Spielwerte auf Anfang zurück und startet die Runde."""
        self.balloons.clear()
        self.particles.clear()
        self.floating_texts.clear()
        self.score = 0.0
        self.balloons_spawned = 0
        self.balloons_popped = 0
        self.total_clicks = 0
        self.accuracy_sum = 0.0
        self.spawn_timer = 0.5  # Erster Ballon erscheint nach 0.5s
        self.current_spawn_interval = 1.6
        self.escaped_balloon = None
        self.last_saved_rank = -1
        self.is_victory = False
        self.state = STATE_PLAYING

    def spawn_balloon(self):
        """Erzeugt den nächsten Ballon bis zur Grenze von 99."""
        if self.balloons_spawned < TOTAL_BALLOONS:
            self.balloons_spawned += 1
            new_balloon = Balloon(self.balloons_spawned, SCREEN_WIDTH, SCREEN_HEIGHT)
            self.balloons.append(new_balloon)

            # Dynamische Steigerung: Je mehr Ballons erschienen sind,
            # desto kürzer werden die Abstände (von 1.6s auf bis zu 0.75s)
            progress = self.balloons_spawned / TOTAL_BALLOONS
            self.current_spawn_interval = max(0.75, 1.6 - progress * 0.85)

    def handle_click(self, pos: tuple[int, int]):
        """Verarbeitet Klicks während des Spiels."""
        self.total_clicks += 1
        mx, my = pos

        # Ballons von oben nach unten (jüngste/oberste zuerst) durchsuchen
        for balloon in reversed(self.balloons):
            if not balloon.popped and balloon.is_more_than_half_visible:
                hit, points, accuracy = balloon.check_click(mx, my)
                if hit:
                    self.balloons_popped += 1
                    self.score += points
                    self.accuracy_sum += accuracy

                    # Sound abspielen
                    self.sounds.play_pop(balloon.tier)

                    # Partikel erzeugen
                    for _ in range(16):
                        self.particles.append(Particle(balloon.x, balloon.y, balloon.color))

                    # Schwebende Punkteanzeige
                    self.floating_texts.append(
                        FloatingText(balloon.x, balloon.y - 10, points, accuracy, self.font_hud)
                    )
                    break  # Nur einen Ballon pro Klick treffen

    def end_round(self, won: bool, reason: str = "", escaped_balloon=None):
        """Beendet die Runde, speichert Lebenszeit-Statistiken und prüft Highscore-Qualifikation."""
        self.is_victory = won
        self.end_game_reason = reason
        self.escaped_balloon = escaped_balloon
        self.last_saved_rank = -1

        # 1. Lebenszeit-Statistiken sofort erfassen
        self.score_manager.record_game_finished(won, self.balloons_popped, self.total_clicks)

        # 2. Prüfen, ob der Score für die Bestenliste qualifiziert ist
        if self.score > 0 and self.score_manager.is_high_score(self.score):
            self.state = STATE_NAME_INPUT
        else:
            self.state = STATE_WON if won else STATE_GAMEOVER

    def submit_high_score(self):
        """Speichert den Highscore mit dem eingegebenen Spielernamen und öffnet das Leaderboard."""
        name = self.player_input_name.strip() or "SPIELER"
        avg_acc = (self.accuracy_sum / self.balloons_popped * 100) if self.balloons_popped > 0 else 0.0
        self.last_saved_rank = self.score_manager.add_score(
            name=name,
            score=self.score,
            popped=self.balloons_popped,
            accuracy_pct=avg_acc,
            won=self.is_victory,
            clicks=self.total_clicks,
        )
        self.sounds.play_victory()
        self.state = STATE_LEADERBOARD

    def handle_name_input_key(self, event: pygame.event.Event):
        """Verarbeitet Tastatureingaben für den Spielernamen."""
        if event.key == pygame.K_RETURN:
            self.submit_high_score()
        elif event.key == pygame.K_BACKSPACE:
            self.player_input_name = self.player_input_name[:-1]
        elif event.key == pygame.K_ESCAPE:
            # Eintrag überspringen und direkt zum Endscreen wechseln
            self.state = STATE_WON if self.is_victory else STATE_GAMEOVER
        else:
            # Nur druckbare Zeichen (Buchstaben, Ziffern, Leerzeichen, Bindestriche, Punkte)
            if len(self.player_input_name) < 10 and event.unicode:
                char = event.unicode.upper()
                if char.isalnum() or char in (" ", "-", "_", "."):
                    self.player_input_name += char

    def update(self, dt: float):
        """Spiellogik aktualisieren."""
        if self.state != STATE_PLAYING:
            return

        # 1. Spawner aktualisieren
        if self.balloons_spawned < TOTAL_BALLOONS:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self.spawn_balloon()
                self.spawn_timer = self.current_spawn_interval + random.uniform(-0.15, 0.15)

        # 2. Ballons bewegen & Sudden Death prüfen
        for balloon in self.balloons:
            if not balloon.popped:
                balloon.update(dt)

                # Prüfen, ob der Ballon die obere Kante erreicht hat
                if balloon.reached_top_edge:
                    self.sounds.play_game_over()
                    self.end_round(
                        won=False,
                        reason="Ein Ballon hat die Oberkante erreicht!",
                        escaped_balloon=balloon,
                    )
                    return

        # Geplatzte Ballons aufräumen
        self.balloons = [b for b in self.balloons if not b.popped]

        # 3. Siegbedingung prüfen: Alle 99 gespawnt und keine mehr aktiv
        if self.balloons_spawned >= TOTAL_BALLOONS and len(self.balloons) == 0:
            self.sounds.play_victory()
            self.end_round(won=True, reason="Alle 99 Luftballons wurden zerplatzt!")
            return

        # 4. Partikel & Texte aktualisieren
        self.particles = [p for p in self.particles if p.update(dt)]
        self.floating_texts = [ft for ft in self.floating_texts if ft.update(dt)]

    def draw_hud(self):
        """Zeichnet die obere Statusleiste."""
        top_bar_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 48)
        pygame.draw.rect(self.screen, TOP_BAR_COLOR, top_bar_rect)
        pygame.draw.line(self.screen, CARD_BORDER, (0, 48), (SCREEN_WIDTH, 48), 1)

        # Punktestand
        score_surf = self.font_hud.render(f"PUNKTE: {self.score:.1f}", True, GOLD)
        self.screen.blit(score_surf, (20, 12))

        # Ballon-Zähler (Geplatzt / 99)
        counter_surf = self.font_hud.render(
            f"BALLONS: {self.balloons_popped} / {TOTAL_BALLOONS}", True, WHITE
        )
        counter_rect = counter_surf.get_rect(center=(SCREEN_WIDTH // 2, 24))
        self.screen.blit(counter_surf, counter_rect)

        # Durchschnittliche Genauigkeit
        avg_acc = (self.accuracy_sum / self.balloons_popped * 100) if self.balloons_popped > 0 else 100.0
        acc_surf = self.font_hud.render(f"PRÄZISION: {avg_acc:.0f}%", True, GREEN)
        self.screen.blit(acc_surf, (SCREEN_WIDTH - acc_surf.get_width() - 20, 12))

        # Gefahren-Warnung an der oberen Kante
        highest_balloon = min([b.y - b.radius for b in self.balloons if not b.popped], default=9999)
        if highest_balloon < 130:
            glow_intensity = max(0, min(255, int((130 - highest_balloon) / 130 * 255)))
            warning_surf = pygame.Surface((SCREEN_WIDTH, 4), pygame.SRCALPHA)
            warning_surf.fill((255, 40, 40, glow_intensity))
            self.screen.blit(warning_surf, (0, 48))

    def draw_start_screen(self):
        """Zeigt den Erklärungs- und Startbildschirm."""
        self.screen.fill(BG_COLOR)

        # Titel
        title_surf = self.font_title.render("99 LUFTBALLONS 🎈", True, WHITE)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 85))
        self.screen.blit(title_surf, title_rect)

        subtitle = self.font_main.render("Präzisions-Arcadespiel", True, GOLD)
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, 130)))

        # Highscore-Plakette
        all_time_high = self.score_manager.get_all_time_high()
        if all_time_high > 0:
            high_text = f"🏆 REKORD: {all_time_high:.1f} Pkt."
            high_surf = self.font_hud.render(high_text, True, GOLD)
            high_rect = high_surf.get_rect(center=(SCREEN_WIDTH // 2, 165))
            pill_rect = high_rect.inflate(30, 8)
            pygame.draw.rect(self.screen, CARD_BG, pill_rect, border_radius=12)
            pygame.draw.rect(self.screen, GOLD, pill_rect, width=1, border_radius=12)
            self.screen.blit(high_surf, high_rect)

        # Regel-Box
        box_rect = pygame.Rect(70, 195, SCREEN_WIDTH - 140, 360)
        pygame.draw.rect(self.screen, CARD_BG, box_rect, border_radius=12)
        pygame.draw.rect(self.screen, CARD_BORDER, box_rect, width=2, border_radius=12)

        rules = [
            "REGELN & SPIELABLAUF:",
            "",
            "• Es steigen insgesamt genau 99 Luftballons von unten auf.",
            "• 50%-Regel: Klickbar erst, wenn mehr als die Hälfte sichtbar ist.",
            "• Präzision zählt: Volltreffer im Zentrum = 100% der Punkte.",
            "  Je weiter am Rand getroffen wird, desto weniger Punkte (bis zu 10%).",
            "• Punkte nach Größe (klein = schwieriger = mehr Punkte):",
            "    1,00 cm (5 Pkt.)  •  1,25 cm (4 Pkt.)  •  1,50 cm (3 Pkt.)",
            "    1,75 cm (2 Pkt.)  •  2,00 cm (1 Pkt.)",
            "",
            "• ACHTUNG: Erreicht ein einziger Ballon die Oberkante, ist das Spiel vorbei!",
        ]

        y_offset = 212
        for line in rules:
            if line.startswith("REGELN") or line.startswith("• ACHTUNG"):
                color = RED if line.startswith("• ACHTUNG") else GOLD
                font = self.font_heading if line.startswith("REGELN") else self.font_main
            else:
                color = WHITE
                font = self.font_main
            text_surf = font.render(line, True, color)
            self.screen.blit(text_surf, (95, y_offset))
            y_offset += 26

        # Start- & Highscore-Aufforderung
        pulse = (math.sin(time.time() * 4) + 1) / 2
        pulse_color = (int(200 + 55 * pulse), int(200 + 55 * pulse), 255)
        start_surf = self.font_heading.render(">> KLICKE ZUM STARTEN <<", True, pulse_color)
        self.screen.blit(start_surf, start_surf.get_rect(center=(SCREEN_WIDTH // 2, 595)))

        sub_nav = self.font_main.render("Drücke [H] für Bestenliste / Hall of Fame", True, GOLD)
        self.screen.blit(sub_nav, sub_nav.get_rect(center=(SCREEN_WIDTH // 2, 638)))

    def draw_name_input_screen(self):
        """Zeigt den Tastatur-Eingabebildschirm für die Bestenliste."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))

        # Titel & Beglückwünschung
        title_text = "HERVORRAGEND! 🎉" if self.is_victory else "NEUER HIGHSCORE! 🏆"
        title_color = GREEN if self.is_victory else GOLD
        title_surf = self.font_title.render(title_text, True, title_color)
        self.screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 110)))

        sub_surf = self.font_heading.render("Trage deinen Namen in die Bestenliste ein:", True, WHITE)
        self.screen.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 160)))

        # Statistik-Box
        box = pygame.Rect(SCREEN_WIDTH // 2 - 200, 200, 400, 130)
        pygame.draw.rect(self.screen, CARD_BG, box, border_radius=10)
        pygame.draw.rect(self.screen, CARD_BORDER, box, width=2, border_radius=10)

        avg_acc = (self.accuracy_sum / self.balloons_popped * 100) if self.balloons_popped > 0 else 0.0
        stats = [
            f"Erreichte Punkte:   {self.score:.1f}",
            f"Geplatzte Ballons:  {self.balloons_popped} von {TOTAL_BALLOONS}",
            f"Ø Treffgenauigkeit: {avg_acc:.1f}%",
        ]
        sy = 222
        for s in stats:
            surf = self.font_main.render(s, True, GOLD if "Punkte" in s else WHITE)
            self.screen.blit(surf, (box.x + 35, sy))
            sy += 30

        # Eingabefeld
        input_label = self.font_main.render("Dein Name (max. 10 Zeichen):", True, (180, 190, 210))
        self.screen.blit(input_label, input_label.get_rect(center=(SCREEN_WIDTH // 2, 360)))

        input_box = pygame.Rect(SCREEN_WIDTH // 2 - 160, 385, 320, 52)
        pygame.draw.rect(self.screen, INPUT_BG, input_box, border_radius=8)
        pygame.draw.rect(self.screen, GOLD, input_box, width=2, border_radius=8)

        # Text mit blinkendem Cursor
        cursor = "|" if int(time.time() * 2.5) % 2 == 0 else " "
        display_str = self.player_input_name + cursor
        name_surf = self.font_heading.render(display_str, True, WHITE)
        self.screen.blit(name_surf, name_surf.get_rect(center=input_box.center))

        # Hinweise zur Tastaturbedienung
        pulse = (math.sin(time.time() * 4) + 1) / 2
        p_col = (int(220 + 35 * pulse), int(220 + 35 * pulse), 100)
        enter_surf = self.font_heading.render(">> Drücke [ENTER] zum Speichern <<", True, p_col)
        self.screen.blit(enter_surf, enter_surf.get_rect(center=(SCREEN_WIDTH // 2, 480)))

        esc_surf = self.font_small.render("[ESC] Überspringen ohne Eintrag  •  [BACKSPACE] Löschen", True, GRAY)
        self.screen.blit(esc_surf, esc_surf.get_rect(center=(SCREEN_WIDTH // 2, 530)))

    def draw_leaderboard_screen(self):
        """Zeigt die Highscore-Tabelle und Gesamtstatistiken."""
        self.screen.fill(BG_COLOR)

        # Titel
        title_surf = self.font_title.render("🏆 HALL OF FAME 🎈", True, GOLD)
        self.screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 50)))

        sub_surf = self.font_main.render("Die 10 besten Durchgänge aller Zeiten", True, (180, 190, 210))
        self.screen.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 88)))

        # Tabellen-Box
        box = pygame.Rect(50, 115, SCREEN_WIDTH - 100, 410)
        pygame.draw.rect(self.screen, CARD_BG, box, border_radius=12)
        pygame.draw.rect(self.screen, CARD_BORDER, box, width=2, border_radius=12)

        # Tabellen-Kopfzeile
        headers = [
            ("RANG", box.x + 20),
            ("SPIELER", box.x + 95),
            ("PUNKTE", box.x + 260),
            ("BALLONS", box.x + 375),
            ("PRÄZISION", box.x + 480),
            ("DATUM", box.x + 580),
        ]
        for header, hx in headers:
            h_surf = self.font_hud.render(header, True, (160, 175, 200))
            self.screen.blit(h_surf, (hx, box.y + 14))

        pygame.draw.line(self.screen, CARD_BORDER, (box.x + 10, box.y + 45), (box.x + box.width - 10, box.y + 45), 1)

        # Einträge
        leaderboard = self.score_manager.get_leaderboard()
        row_y = box.y + 54

        if not leaderboard:
            empty_surf = self.font_main.render("Noch keine Einträge vorhanden. Knacke den ersten Rekord!", True, GRAY)
            self.screen.blit(empty_surf, empty_surf.get_rect(center=(SCREEN_WIDTH // 2, box.y + 160)))
        else:
            for idx, entry in enumerate(leaderboard, start=1):
                # Hervorhebung für den soeben gespeicherten Highscore
                is_current = (idx == self.last_saved_rank)
                if is_current:
                    row_rect = pygame.Rect(box.x + 10, row_y - 2, box.width - 20, 28)
                    pygame.draw.rect(self.screen, (50, 68, 115), row_rect, border_radius=6)
                    pygame.draw.rect(self.screen, GOLD, row_rect, width=1, border_radius=6)

                # Rang-Farbe & Medaillen
                if idx == 1:
                    rank_str, rank_color = "1.", GOLD
                elif idx == 2:
                    rank_str, rank_color = "2.", SILVER
                elif idx == 3:
                    rank_str, rank_color = "3.", BRONZE
                else:
                    rank_str, rank_color = f"{idx}.", WHITE

                # Spalteninhalte rendern
                r_surf = self.font_main.render(rank_str, True, rank_color)
                self.screen.blit(r_surf, (box.x + 25, row_y))

                name_color = GOLD if is_current else WHITE
                name_text = entry.get("name", "PLAYER")
                if is_current:
                    name_text += " [NEU]"
                name_surf = self.font_main.render(name_text, True, name_color)
                self.screen.blit(name_surf, (box.x + 95, row_y))

                pts_surf = self.font_main.render(f"{entry.get('score', 0.0):.1f}", True, GOLD)
                self.screen.blit(pts_surf, (box.x + 260, row_y))

                pop_str = f"{entry.get('balloons_popped', 0)}/{TOTAL_BALLOONS}"
                pop_surf = self.font_main.render(pop_str, True, WHITE)
                self.screen.blit(pop_surf, (box.x + 375, row_y))

                acc_str = f"{entry.get('accuracy_pct', 0.0):.0f}%"
                acc_surf = self.font_main.render(acc_str, True, GREEN)
                self.screen.blit(acc_surf, (box.x + 480, row_y))

                date_str = entry.get("date", "")
                date_surf = self.font_small.render(date_str, True, GRAY)
                self.screen.blit(date_surf, (box.x + 580, row_y + 3))

                row_y += 33

        # Lebenszeit-Statistiken-Leiste
        stats = self.score_manager.get_lifetime_stats()
        stats_box = pygame.Rect(50, 540, SCREEN_WIDTH - 100, 48)
        pygame.draw.rect(self.screen, (14, 24, 48), stats_box, border_radius=8)
        pygame.draw.rect(self.screen, CARD_BORDER, stats_box, width=1, border_radius=8)

        stats_line = (
            f"GESAMT:  Gespielte Runden: {stats.get('games_played', 0)}   •   "
            f"Siege: {stats.get('games_won', 0)}   •   "
            f"Ballons zerplatzt: {stats.get('total_popped', 0)}"
        )
        stats_surf = self.font_main.render(stats_line, True, (190, 200, 220))
        self.screen.blit(stats_surf, stats_surf.get_rect(center=stats_box.center))

        # Steuerungs-Hinweise
        pulse = (math.sin(time.time() * 4) + 1) / 2
        p_col = (int(220 + 35 * pulse), int(220 + 35 * pulse), 100)
        nav_surf = self.font_heading.render("Drücke [R] für ein neues Spiel  •  [ESC] / [H] zum Menü", True, p_col)
        self.screen.blit(nav_surf, nav_surf.get_rect(center=(SCREEN_WIDTH // 2, 630)))

    def draw_game_over_screen(self):
        """Zeigt den Game-Over-Bildschirm bei Sudden Death."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))

        go_surf = self.font_title.render("GAME OVER", True, RED)
        self.screen.blit(go_surf, go_surf.get_rect(center=(SCREEN_WIDTH // 2, 150)))

        reason_surf = self.font_heading.render(
            self.end_game_reason or "Ein Ballon hat die Oberkante erreicht!", True, WHITE
        )
        self.screen.blit(reason_surf, reason_surf.get_rect(center=(SCREEN_WIDTH // 2, 205)))

        # Statistik-Kasten
        box = pygame.Rect(SCREEN_WIDTH // 2 - 200, 245, 400, 235)
        pygame.draw.rect(self.screen, CARD_BG, box, border_radius=10)
        pygame.draw.rect(self.screen, CARD_BORDER, box, width=2, border_radius=10)

        avg_acc = (self.accuracy_sum / self.balloons_popped * 100) if self.balloons_popped > 0 else 0.0
        all_time_high = self.score_manager.get_all_time_high()
        stats = [
            f"Erreichte Punkte:   {self.score:.1f}",
            f"Allzeit-Rekord:     {all_time_high:.1f}",
            f"Geplatzte Ballons:  {self.balloons_popped} von {TOTAL_BALLOONS}",
            f"Ø Treffgenauigkeit: {avg_acc:.1f}%",
            f"Klicks gesamt:      {self.total_clicks}",
        ]
        sy = 265
        for s in stats:
            surf = self.font_main.render(s, True, GOLD if "Punkte" in s else WHITE)
            self.screen.blit(surf, (box.x + 35, sy))
            sy += 35

        # Steuerungs-Hinweise
        pulse = (math.sin(time.time() * 4) + 1) / 2
        p_col = (int(220 + 35 * pulse), int(220 + 35 * pulse), 100)
        restart_surf = self.font_heading.render("Drücke [R] für Neustart  •  [H] für Bestenliste", True, p_col)
        self.screen.blit(restart_surf, restart_surf.get_rect(center=(SCREEN_WIDTH // 2, 530)))

    def draw_won_screen(self):
        """Zeigt den Siegesbildschirm, wenn alle 99 Ballons zerplatzt wurden."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 34, 42, 220))
        self.screen.blit(overlay, (0, 0))

        win_surf = self.font_title.render("HERVORRAGEND! 🎉", True, GOLD)
        self.screen.blit(win_surf, win_surf.get_rect(center=(SCREEN_WIDTH // 2, 150)))

        sub_surf = self.font_heading.render("Alle 99 Luftballons wurden zerplatzt!", True, GREEN)
        self.screen.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 205)))

        # Statistik-Kasten
        box = pygame.Rect(SCREEN_WIDTH // 2 - 200, 245, 400, 235)
        pygame.draw.rect(self.screen, (20, 48, 56), box, border_radius=10)
        pygame.draw.rect(self.screen, (38, 90, 80), box, width=2, border_radius=10)

        avg_acc = (self.accuracy_sum / self.balloons_popped * 100) if self.balloons_popped > 0 else 0.0
        all_time_high = self.score_manager.get_all_time_high()
        stats = [
            f"FINALER SPIELSTAND: {self.score:.1f}",
            f"Allzeit-Rekord:     {all_time_high:.1f}",
            f"Trefferquote:      {self.balloons_popped} / {TOTAL_BALLOONS} (100%)",
            f"Ø Treffgenauigkeit: {avg_acc:.1f}%",
            f"Klicks gesamt:      {self.total_clicks}",
        ]
        sy = 265
        for s in stats:
            surf = self.font_main.render(s, True, GOLD if "SPIELSTAND" in s else WHITE)
            self.screen.blit(surf, (box.x + 35, sy))
            sy += 35

        restart_surf = self.font_heading.render("Drücke [R] für Neustart  •  [H] für Bestenliste", True, WHITE)
        self.screen.blit(restart_surf, restart_surf.get_rect(center=(SCREEN_WIDTH // 2, 530)))

    def draw_custom_crosshair(self, mouse_pos: tuple[int, int]):
        """Zeichnet ein dezentes Fadenkreuz für präzises Zielen."""
        mx, my = mouse_pos
        pygame.draw.circle(self.screen, (255, 255, 255), (mx, my), 2)
        pygame.draw.line(self.screen, (255, 255, 255), (mx - 10, my), (mx - 4, my), 1)
        pygame.draw.line(self.screen, (255, 255, 255), (mx + 4, my), (mx + 10, my), 1)
        pygame.draw.line(self.screen, (255, 255, 255), (mx, my - 10), (mx, my - 4), 1)
        pygame.draw.line(self.screen, (255, 255, 255), (mx, my + 4), (mx, my + 10), 1)

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta-Zeit in Sekunden

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == STATE_START:
                        self.reset_game()
                    elif self.state == STATE_PLAYING:
                        self.handle_click(event.pos)
                    elif self.state in (STATE_GAMEOVER, STATE_WON):
                        self.reset_game()
                    elif self.state == STATE_LEADERBOARD:
                        self.state = STATE_START

                elif event.type == pygame.KEYDOWN:
                    if self.state == STATE_NAME_INPUT:
                        self.handle_name_input_key(event)

                    elif self.state == STATE_LEADERBOARD:
                        if event.key in (pygame.K_ESCAPE, pygame.K_h):
                            self.state = STATE_START
                        elif event.key in (pygame.K_r, pygame.K_SPACE):
                            self.reset_game()

                    elif self.state == STATE_START:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                        elif event.key == pygame.K_h:
                            self.state = STATE_LEADERBOARD
                        elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                            self.reset_game()

                    elif self.state == STATE_PLAYING:
                        if event.key == pygame.K_ESCAPE:
                            running = False

                    elif self.state in (STATE_GAMEOVER, STATE_WON):
                        if event.key == pygame.K_ESCAPE:
                            running = False
                        elif event.key == pygame.K_r:
                            self.reset_game()
                        elif event.key == pygame.K_h:
                            self.state = STATE_LEADERBOARD

            # Spiellogik
            self.update(dt)

            # Zeichnen
            if self.state == STATE_START:
                self.draw_start_screen()
            elif self.state == STATE_LEADERBOARD:
                self.draw_leaderboard_screen()
            else:
                self.screen.fill(BG_COLOR)

                # Ballons zeichnen
                for balloon in self.balloons:
                    balloon.draw(self.screen)

                # Partikel & aufsteigende Punkte
                for p in self.particles:
                    p.draw(self.screen)
                for ft in self.floating_texts:
                    ft.draw(self.screen)

                # HUD & Ränder
                self.draw_hud()

                if self.state == STATE_GAMEOVER:
                    self.draw_game_over_screen()
                elif self.state == STATE_WON:
                    self.draw_won_screen()
                elif self.state == STATE_NAME_INPUT:
                    self.draw_name_input_screen()

            # Fadenkreuz im Spiel zeichnen
            if self.state == STATE_PLAYING and pygame.mouse.get_focused():
                self.draw_custom_crosshair(pygame.mouse.get_pos())

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
