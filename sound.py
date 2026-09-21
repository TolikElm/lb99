"""
sound.py - Prozedurale Soundeffekte für 99-Luftballons
Erzeugt Audio-Wellenformen direkt im Speicher (ohne externe Sounddateien).
"""

import math
import struct
import pygame

SAMPLE_RATE = 44100

class SoundManager:
    def __init__(self):
        self.enabled = False
        try:
            # Versuche Pygame Mixer mit 16-bit Mono zu initialisieren
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
            self.enabled = True
            # Cache für generierte Sounds (5 Größenstufen + Extra-Sounds)
            self._pop_sounds = {}
            self._gameover_sound = None
            self._victory_sound = None
            self._init_sounds()
        except Exception as e:
            print(f"[SoundManager] Audio-Initialisierung nicht verfügbar: {e}")
            self.enabled = False

    def _generate_sine_pcm(self, start_freq: float, end_freq: float, duration: float, volume: float = 0.3) -> bytes:
        """Erzeugt 16-Bit-Mono-PCM-Daten für einen Frequenz-Slide mit exponentiellem Abfall."""
        n_samples = int(SAMPLE_RATE * duration)
        buf = bytearray()
        for i in range(n_samples):
            t = i / SAMPLE_RATE
            progress = t / duration
            # Frequenz fällt oder steigt gleichmäßig
            current_freq = start_freq + (end_freq - start_freq) * progress
            # Exponentielle Hüllkurve für knackigen Anschlag
            envelope = math.exp(-22 * progress)
            value = int(32767 * volume * envelope * math.sin(2 * math.pi * current_freq * t))
            # 16-bit signed integer clamped
            value = max(-32768, min(32767, value))
            buf.extend(struct.pack("<h", value))
        return bytes(buf)

    def _init_sounds(self):
        if not self.enabled:
            return
        try:
            # 5 Stufen: Stufe 1 (kleinster Ballon) = hell/hoch (900 -> 250 Hz)
            # bis Stufe 5 (größter Ballon) = tief/bassig (350 -> 80 Hz)
            freq_map = {
                1: (950, 300),
                2: (800, 240),
                3: (650, 180),
                4: (500, 130),
                5: (360, 80),
            }
            for tier, (f_start, f_end) in freq_map.items():
                pcm = self._generate_sine_pcm(f_start, f_end, duration=0.08, volume=0.35)
                self._pop_sounds[tier] = pygame.mixer.Sound(buffer=pcm)

            # Game Over Sound (absteigende Töne)
            n_samples = int(SAMPLE_RATE * 0.4)
            go_buf = bytearray()
            for i in range(n_samples):
                t = i / SAMPLE_RATE
                f = 280 - 180 * (t / 0.4)
                env = max(0.0, 1.0 - t / 0.4)
                val = int(32767 * 0.4 * env * math.sin(2 * math.pi * f * t))
                go_buf.extend(struct.pack("<h", max(-32768, min(32767, val))))
            self._gameover_sound = pygame.mixer.Sound(buffer=bytes(go_buf))

            # Sieg-Sound (heller zweistufiger Chime)
            n_samples_vic = int(SAMPLE_RATE * 0.5)
            vic_buf = bytearray()
            for i in range(n_samples_vic):
                t = i / SAMPLE_RATE
                f = 523.25 if t < 0.25 else 783.99  # C5 zu G5
                env = math.exp(-8 * (t % 0.25))
                val = int(32767 * 0.35 * env * math.sin(2 * math.pi * f * t))
                vic_buf.extend(struct.pack("<h", max(-32768, min(32767, val))))
            self._victory_sound = pygame.mixer.Sound(buffer=bytes(vic_buf))

        except Exception as e:
            print(f"[SoundManager] Fehler bei Sound-Synthese: {e}")
            self.enabled = False

    def play_pop(self, tier: int):
        """Spielt den passenden Plopp-Ton für die Ballongröße."""
        if not self.enabled:
            return
        sound = self._pop_sounds.get(tier)
        if sound:
            sound.play()

    def play_game_over(self):
        if self.enabled and self._gameover_sound:
            self._gameover_sound.play()

    def play_victory(self):
        if self.enabled and self._victory_sound:
            self._victory_sound.play()
