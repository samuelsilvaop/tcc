from __future__ import annotations

import os
from pathlib import Path

import pygame.mixer

from midi_game.config import load_config

MIDI_FOLDER = Path(__file__).parent / "assets" / "midi"


def play_music(midi_filename, volume=None):
    base = os.path.splitext(midi_filename)[0]
    ogg_file = os.path.join(MIDI_FOLDER, f"{base}.ogg")

    if not os.path.exists(ogg_file):
        print(f"⚠️ Sem áudio para {midi_filename} (arquivo {base}.ogg não existe).")
        return

    if not pygame.mixer.get_init():
        pygame.mixer.init()

    if volume is None:
        volume = float(load_config().get("music_volume", 0.7))

    pygame.mixer.music.load(ogg_file)
    pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
    pygame.mixer.music.play()


def stop_music():
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
