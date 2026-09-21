"""
balloon.py - Ballon-Modell & Spielmechanik
Verwaltet 5 Größenstufen, Bewegung, 50%-Auftauchregel und Treffer-Genauigkeit.
"""

import math
import random
import pygame

# Definition der 5 Ballon-Klassen
# 1 cm entspricht ca. 40 Pixeln Durchmesser (20 px Radius) bei Standard-DPI
BALLOON_SPECS = [
    {"tier": 1, "cm": 1.00, "radius": 20, "points": 5, "color": (235, 55, 65)},    # Rot
    {"tier": 2, "cm": 1.25, "radius": 25, "points": 4, "color": (245, 125, 35)},   # Orange
    {"tier": 3, "cm": 1.50, "radius": 30, "points": 3, "color": (240, 200, 45)},   # Gelb
    {"tier": 4, "cm": 1.75, "radius": 35, "points": 2, "color": (50, 195, 110)},   # Grün
    {"tier": 5, "cm": 2.00, "radius": 40, "points": 1, "color": (65, 145, 245)},   # Blau
]

class Balloon:
    def __init__(self, balloon_id: int, screen_width: int, screen_height: int, tier: int = None):
        self.id = balloon_id
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Zufällige Stufe 1 bis 5 auswählen, falls nicht vorgegeben
        if tier is None:
            spec = random.choice(BALLOON_SPECS)
        else:
            spec = next(s for s in BALLOON_SPECS if s["tier"] == tier)

        self.tier = spec["tier"]
        self.cm = spec["cm"]
        self.radius = spec["radius"]
        self.base_points = spec["points"]
        self.color = spec["color"]

        # Horizontale Startposition mit Sicherheitsabstand zu den Rändern
        margin = self.radius + 15
        self.base_x = random.uniform(margin, screen_width - margin)
        self.x = self.base_x

        # Startet unterhalb des sichtbaren Bildschirms
        self.y = screen_height + self.radius + 10.0

        # Aufstiegsgeschwindigkeit (in Pixeln pro Sekunde)
        # Kleinere Ballons steigen etwas zügiger
        speed_bonus = (5 - self.tier) * 6.0
        self.speed_y = random.uniform(70, 95) + speed_bonus

        # Sanftes horizontales Schaukeln (Wind-Effekt)
        self.wobble_amplitude = random.uniform(8, 20)
        self.wobble_speed = random.uniform(1.8, 3.2)
        self.wobble_phase = random.uniform(0, 2 * math.pi)

        self.popped = False

    @property
    def is_more_than_half_visible(self) -> bool:
        """
        Prüft die 50%-Regel:
        Der Ballon ist mehr als zur Hälfte sichtbar, wenn sein Mittelpunkt (y)
        die untere Bildschirmkante (screen_height) überschritten hat.
        """
        return self.y < self.screen_height

    @property
    def reached_top_edge(self) -> bool:
        """
        Prüft, ob der Ballon mit der Oberkante den oberen Bildschirmrand berührt.
        Top-Kante ist y - radius <= 0.
        """
        return (self.y - self.radius) <= 0

    def update(self, dt: float):
        """Bewegt den Ballon nach oben und wendet Schaukeln an."""
        self.y -= self.speed_y * dt
        self.wobble_phase += self.wobble_speed * dt
        self.x = self.base_x + math.sin(self.wobble_phase) * self.wobble_amplitude
        # Sicherstellen, dass er innerhalb der seitlichen Ränder bleibt
        self.x = max(self.radius, min(self.screen_width - self.radius, self.x))

    def calculate_alpha(self) -> int:
        """
        Berechnet die Farbintensität (Alpha):
        - Ganz unten blass (ca. 70 Alpha)
        - Bei 50% Sichtbarkeit (y == screen_height): ca. 165 Alpha
        - Komplett auf dem Bildschirm (y <= screen_height - radius): 255 (volle Intensität)
        """
        if self.y <= self.screen_height - self.radius:
            return 255
        elif self.y >= self.screen_height + self.radius:
            return 70
        else:
            # Linear von 70 auf 255 interpolieren
            progress = ( (self.screen_height + self.radius) - self.y ) / (2 * self.radius)
            return int(70 + (255 - 70) * max(0.0, min(1.0, progress)))

    def check_click(self, mouse_x: int, mouse_y: int) -> tuple[bool, float, float]:
        """
        Prüft, ob der Ballon angeklickt wurde.
        Bedingungen:
        1. Noch nicht geplatzt
        2. Mehr als die Hälfte sichtbar (50%-Regel)
        3. Klick innerhalb des Kreisradius

        Rückgabe: (hit, points, accuracy)
        """
        if self.popped:
            return False, 0.0, 0.0

        # Darf erst angeklickt werden, wenn mehr als die Hälfte sichtbar ist
        if not self.is_more_than_half_visible:
            return False, 0.0, 0.0

        dist = math.hypot(mouse_x - self.x, mouse_y - self.y)
        if dist <= self.radius:
            self.popped = True
            # Treffpunkt-Präzision:
            # 100% (1.0) bei dist == 0
            # 10% (0.1) bei dist == radius
            norm_dist = dist / self.radius
            accuracy = 1.0 - 0.9 * norm_dist
            accuracy = max(0.1, min(1.0, accuracy))
            points = round(self.base_points * accuracy, 1)
            return True, points, accuracy

        return False, 0.0, 0.0

    def draw(self, surface: pygame.Surface):
        """Zeichnet den Ballon mit Transparenz, Schnur und Glanzpunkt."""
        if self.popped:
            return

        alpha = self.calculate_alpha()
        r = self.radius
        surf_size = int(r * 2 + 20)
        temp_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        center = (surf_size // 2, r + 4)

        # 1. Bändchen / Schnur unten am Ballon
        knot_y = center[1] + r
        string_color = (180, 180, 190, min(alpha, 190))
        pts = [
            (center[0], knot_y),
            (center[0] + 3, knot_y + 8),
            (center[0] - 2, knot_y + 16),
            (center[0] + 1, knot_y + 24),
        ]
        pygame.draw.lines(temp_surf, string_color, False, pts, 2)

        # Kleiner Knoten
        knot_color = (*self.color, alpha)
        pygame.draw.polygon(temp_surf, knot_color, [
            (center[0] - 3, knot_y - 1),
            (center[0] + 3, knot_y - 1),
            (center[0], knot_y + 4),
        ])

        # 2. Ballon-Körper (Kreis)
        body_color = (*self.color, alpha)
        pygame.draw.circle(temp_surf, body_color, center, r)

        # 3. Wenn noch nicht klickbar (< 50% sichtbar), dezenten Hinweis-Rahmen
        if not self.is_more_than_half_visible:
            # Gestrichelter oder blasser Rand
            pygame.draw.circle(temp_surf, (255, 255, 255, int(alpha * 0.5)), center, r, 1)
        else:
            # Dezenter Glanz-Punkt oben links für 3D-Look
            shine_alpha = int(alpha * 0.45)
            shine_color = (255, 255, 255, shine_alpha)
            shine_pos = (int(center[0] - r * 0.35), int(center[1] - r * 0.35))
            shine_r = max(2, int(r * 0.22))
            pygame.draw.circle(temp_surf, shine_color, shine_pos, shine_r)

        # Auf Haupt-Surface zeichnen
        blit_x = int(self.x - center[0])
        blit_y = int(self.y - center[1])
        surface.blit(temp_surf, (blit_x, blit_y))
