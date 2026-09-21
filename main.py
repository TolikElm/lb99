"""
main.py - 99-Luftballons Hauptprogramm
Ein Geschicklichkeitsspiel in Pygame.
"""

import sys
import time
import random
import pygame

from balloon import Balloon, BALLOON_SPECS
from effects import Particle, FloatingText
from sound import SoundManager

# Fenster-Dimensionen
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60

# Farbdefinitionen
BG_COLOR = (24, 28, 38)
TOP_BAR_COLOR = (16, 19, 26)
WHITE = (250, 250, 250)
GRAY = (140, 145, 160)
GOLD = (255, 215, 0)
RED = (240, 60, 60)
GREEN = (60, 220, 120)

# Spielzustände
STATE_START = "START"
STATE_PLAYING = "PLAYING"
STATE_GAMEOVER = "GAMEOVER"
STATE_WON = "WON"

TOTAL_BALLOONS = 99


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("99-Luftballons 🎈")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        # Schriftarten laden (Fallback auf Standardschrift)
        self.font_title = pygame.font.SysFont("Helvetica", 46, bold=True)
        self.font_heading = pygame.font.SysFont("Helvetica", 28, bold=True)
        self.font_main = pygame.font.SysFont("Helvetica", 20)
        self.font_small = pygame.font.SysFont("Helvetica", 16)
        self.font_hud = pygame.font.SysFont("Helvetica", 22, bold=True)

        self.sounds = SoundManager()
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

    def reset_game(self):
        """Setzt alle Spielwerte auf Anfang zurück."""
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
        hit_any = False
        for balloon in reversed(self.balloons):
            if not balloon.popped and balloon.is_more_than_half_visible:
                hit, points, accuracy = balloon.check_click(mx, my)
                if hit:
                    hit_any = True
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
                    self.state = STATE_GAMEOVER
                    self.escaped_balloon = balloon
                    self.sounds.play_game_over()
                    return

        # Geplatzte Ballons aufräumen
        self.balloons = [b for b in self.balloons if not b.popped]

        # 3. Siegbedingung prüfen: Alle 99 gespawnt und keine mehr aktiv
        if self.balloons_spawned >= TOTAL_BALLOONS and len(self.balloons) == 0:
            self.state = STATE_WON
            self.sounds.play_victory()

        # 4. Partikel & Texte aktualisieren
        self.particles = [p for p in self.particles if p.update(dt)]
        self.floating_texts = [ft for ft in self.floating_texts if ft.update(dt)]

    def draw_hud(self):
        """Zeichnet obere Statusleiste."""
        # Hintergrundleiste oben
        top_bar_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 48)
        pygame.draw.rect(self.screen, TOP_BAR_COLOR, top_bar_rect)
        pygame.draw.line(self.screen, (40, 48, 65), (0, 48), (SCREEN_WIDTH, 48), 1)

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

        # Gefahren-Warnung an der oberen Kante, falls ein Ballon nahe ist
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
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title_surf, title_rect)

        subtitle = self.font_main.render("Präzisions-Arcadespiel", True, GOLD)
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, 150)))

        # Regel-Box
        box_rect = pygame.Rect(70, 190, SCREEN_WIDTH - 140, 360)
        pygame.draw.rect(self.screen, (32, 38, 52), box_rect, border_radius=12)
        pygame.draw.rect(self.screen, (55, 65, 88), box_rect, width=2, border_radius=12)

        rules = [
            "REGELN & SPIELABLAUF:",
            "",
            "• Es steigen insgesamt genau 99 Luftballons von unten auf.",
            "• 50%-Regel: Ein Ballon darf ERST angeklickt werden, wenn mehr als",
            "  die Hälfte sichtbar ist (er gewinnt beim Aufsteigen an Farbe).",
            "• Präzision zählt: Volltreffer im Zentrum = 100% der Punkte.",
            "  Je weiter am Rand getroffen wird, desto weniger Punkte (bis zu 10%).",
            "• Punkte nach Größe (klein = schwieriger = mehr Punkte):",
            "    1,00 cm (5 Pkt.)  •  1,25 cm (4 Pkt.)  •  1,50 cm (3 Pkt.)",
            "    1,75 cm (2 Pkt.)  •  2,00 cm (1 Pkt.)",
            "",
            "• ACHTUNG: Erreicht ein einziger Ballon die Oberkante, ist das Spiel vorbei!",
        ]

        y_offset = 210
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

        # Start-Aufforderung mit sanftem Blinken
        pulse = (math.sin(time.time() * 4) + 1) / 2
        pulse_color = (int(200 + 55 * pulse), int(200 + 55 * pulse), 255)
        start_surf = self.font_heading.render(">> KLICKE MIT DER MAUS ZUM STARTEN <<", True, pulse_color)
        self.screen.blit(start_surf, start_surf.get_rect(center=(SCREEN_WIDTH // 2, 600)))

    def draw_game_over_screen(self):
        """Zeigt den Game-Over-Bildschirm bei Sudden Death."""
        # Halbtransparenter dunkler Schleier über dem Spielfeld
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 15, 22, 210))
        self.screen.blit(overlay, (0, 0))

        # Titel
        go_surf = self.font_title.render("GAME OVER", True, RED)
        self.screen.blit(go_surf, go_surf.get_rect(center=(SCREEN_WIDTH // 2, 170)))

        reason_surf = self.font_heading.render("Ein Ballon hat die Oberkante erreicht!", True, WHITE)
        self.screen.blit(reason_surf, reason_surf.get_rect(center=(SCREEN_WIDTH // 2, 230)))

        # Statistik-Kasten
        box = pygame.Rect(SCREEN_WIDTH // 2 - 200, 275, 400, 210)
        pygame.draw.rect(self.screen, (32, 38, 52), box, border_radius=10)
        pygame.draw.rect(self.screen, (60, 70, 95), box, width=2, border_radius=10)

        avg_acc = (self.accuracy_sum / self.balloons_popped * 100) if self.balloons_popped > 0 else 0.0
        stats = [
            f"Erreichte Punkte:   {self.score:.1f}",
            f"Geplatzte Ballons:  {self.balloons_popped} von {TOTAL_BALLOONS}",
            f"Ø Treffgenauigkeit: {avg_acc:.1f}%",
            f"Klicks gesamt:      {self.total_clicks}",
        ]
        sy = 300
        for s in stats:
            surf = self.font_main.render(s, True, WHITE)
            self.screen.blit(surf, (box.x + 35, sy))
            sy += 38

        # Neustart-Hinweis
        pulse = (math.sin(time.time() * 4) + 1) / 2
        p_col = (int(220 + 35 * pulse), int(220 + 35 * pulse), 100)
        restart_surf = self.font_heading.render("Drücke [R] oder Klicke für ein neues Spiel", True, p_col)
        self.screen.blit(restart_surf, restart_surf.get_rect(center=(SCREEN_WIDTH // 2, 535)))

    def draw_won_screen(self):
        """Zeigt den Siegesbildschirm, wenn alle 99 Ballons zerplatzt wurden."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 25, 20, 215))
        self.screen.blit(overlay, (0, 0))

        win_surf = self.font_title.render("HERVORRAGEND! 🎉", True, GOLD)
        self.screen.blit(win_surf, win_surf.get_rect(center=(SCREEN_WIDTH // 2, 170)))

        sub_surf = self.font_heading.render("Alle 99 Luftballons wurden zerplatzt!", True, GREEN)
        self.screen.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 230)))

        # Statistik-Kasten
        box = pygame.Rect(SCREEN_WIDTH // 2 - 200, 275, 400, 210)
        pygame.draw.rect(self.screen, (28, 48, 40), box, border_radius=10)
        pygame.draw.rect(self.screen, (45, 90, 65), box, width=2, border_radius=10)

        avg_acc = (self.accuracy_sum / self.balloons_popped * 100) if self.balloons_popped > 0 else 0.0
        stats = [
            f"FINALER SPIELSTAND: {self.score:.1f}",
            f"Trefferquote:      {self.balloons_popped} / {TOTAL_BALLOONS} (100%)",
            f"Ø Treffgenauigkeit: {avg_acc:.1f}%",
            f"Klicks gesamt:      {self.total_clicks}",
        ]
        sy = 300
        for s in stats:
            surf = self.font_main.render(s, True, WHITE)
            self.screen.blit(surf, (box.x + 35, sy))
            sy += 38

        restart_surf = self.font_heading.render("Drücke [R] oder Klicke für ein neues Spiel", True, WHITE)
        self.screen.blit(restart_surf, restart_surf.get_rect(center=(SCREEN_WIDTH // 2, 535)))

    def draw_custom_crosshair(self, mouse_pos: tuple[int, int]):
        """Zeichnet ein dezentes Fadenkreuz für präzises Zielen."""
        mx, my = mouse_pos
        ch_color = (255, 255, 255, 180)
        # Kleiner Mittelpunkt und 4 Fadenkreuz-Striche
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
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        self.reset_game()

            # Logik
            self.update(dt)

            # Zeichnen
            if self.state == STATE_START:
                self.draw_start_screen()
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

            # Dezentes Fadenkreuz an der Mausposition zeichnen
            if pygame.mouse.get_focused():
                self.draw_custom_crosshair(pygame.mouse.get_pos())

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
