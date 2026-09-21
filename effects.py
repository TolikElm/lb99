"""
effects.py - Visuelle Partikel & aufsteigende Punkte-Texte
"""

import math
import random
import pygame

class Particle:
    """Ein Farb-Partikel, das beim Zerplatzen eines Ballons wegfliegt."""
    def __init__(self, x: float, y: float, color: tuple):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(60, 220)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.radius = random.uniform(2.5, 5.0)
        self.alpha = 255.0
        self.decay = random.uniform(400, 600)  # Alpha pro Sekunde

    def update(self, dt: float) -> bool:
        """Aktualisiert Position und Alpha. Gibt False zurück, wenn tot."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 180 * dt  # Leichte Schwerkraft
        self.alpha -= self.decay * dt
        return self.alpha > 0

    def draw(self, surface: pygame.Surface):
        if self.alpha <= 0:
            return
        r = int(self.radius)
        if r <= 0:
            return
        temp_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        color_with_alpha = (*self.color[:3], int(max(0, min(255, self.alpha))))
        pygame.draw.circle(temp_surf, color_with_alpha, (r + 1, r + 1), r)
        surface.blit(temp_surf, (self.x - r - 1, self.y - r - 1))


class FloatingText:
    """Zeigt die erzielte Punktzahl und Treffergenauigkeit an der Klickstelle."""
    def __init__(self, x: float, y: float, points: float, accuracy: float, font: pygame.font.Font):
        self.x = x
        self.y = y
        self.points = points
        self.accuracy = accuracy
        self.font = font
        self.alpha = 255.0
        self.lifetime = 0.85  # Sekunden
        self.age = 0.0

        pct = int(accuracy * 100)
        if pct >= 95:
            self.text = f"+{points:.1f} (PERFEKT!)"
            self.color = (255, 220, 60)  # Gold
        elif pct >= 70:
            self.text = f"+{points:.1f} ({pct}%)"
            self.color = (80, 240, 120)  # Hellgrün
        else:
            self.text = f"+{points:.1f} ({pct}%)"
            self.color = (240, 240, 240)  # Weiß/Hellgrau

    def update(self, dt: float) -> bool:
        self.age += dt
        self.y -= 45 * dt  # Steigt langsam nach oben
        self.alpha = max(0.0, 255.0 * (1.0 - (self.age / self.lifetime)))
        return self.age < self.lifetime

    def draw(self, surface: pygame.Surface):
        if self.alpha <= 0:
            return
        rendered = self.font.render(self.text, True, self.color)
        temp_surf = pygame.Surface(rendered.get_size(), pygame.SRCALPHA)
        temp_surf.blit(rendered, (0, 0))
        temp_surf.set_alpha(int(self.alpha))
        # Zentriert an der Position
        rect = temp_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(temp_surf, rect)
