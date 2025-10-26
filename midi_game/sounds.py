import os

import pygame.mixer

MIDI_FOLDER = "midi_game/assets/midi"


def play_music(midi_filename):
    base = os.path.splitext(midi_filename)[0]
    ogg_file = os.path.join(MIDI_FOLDER, f"{base}.ogg")

    if not os.path.exists(ogg_file):
        print(f"⚠️ Arquivo de áudio correspondente não encontrado: {ogg_file}")
        return

    pygame.mixer.init()
    pygame.mixer.music.load(ogg_file)
    pygame.mixer.music.play()
