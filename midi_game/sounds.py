from __future__ import annotations

import os
from pathlib import Path

import pygame.mixer

from midi_game.config import load_config

MIDI_FOLDER = Path(__file__).parent / "assets" / "midi"

# Deve bater com audio_converter.SAMPLE_RATE: evita resample no mixer (custa
# tempo e adiciona latencia variavel entre SO/driver de audio).
MIXER_FREQUENCY = 48000

_loaded_ogg: str | None = None


def preload_music(midi_filename) -> bool:
    """Carrega o .ogg com antecedencia (ex.: durante a contagem 3-2-1), pra
    que play_music() na hora exata do gatilho so precise chamar .play()
    (rapido) em vez de pagar o custo de I/O/decodificacao naquele frame."""
    global _loaded_ogg
    base = os.path.splitext(midi_filename)[0]
    ogg_file = os.path.join(MIDI_FOLDER, f"{base}.ogg")

    if not os.path.exists(ogg_file):
        print(f"⚠️ Sem áudio para {midi_filename} (arquivo {base}.ogg não existe).")
        _loaded_ogg = None
        return False

    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=MIXER_FREQUENCY)

    pygame.mixer.music.load(ogg_file)
    _loaded_ogg = ogg_file
    return True


def play_music(midi_filename, volume=None):
    base = os.path.splitext(midi_filename)[0]
    ogg_file = os.path.join(MIDI_FOLDER, f"{base}.ogg")

    if _loaded_ogg != ogg_file:
        if not preload_music(midi_filename):
            return

    if volume is None:
        volume = float(load_config().get("music_volume", 0.7))

    pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
    pygame.mixer.music.play()


def stop_music():
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
