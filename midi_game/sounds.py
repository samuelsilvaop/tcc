import os

import pygame.mixer

MIDI_FOLDER = "midi_game/assets/midi"


def play_music(midi_filename):
    base = os.path.splitext(midi_filename)[0]
    ogg_file = os.path.join(MIDI_FOLDER, f"{base}.ogg")

    if not os.path.exists(ogg_file):
        print(f"⚠️ Sem áudio para {midi_filename} (arquivo {base}.ogg não existe).")
        return

    if not pygame.mixer.get_init():
        pygame.mixer.init()

    pygame.mixer.music.load(ogg_file)
    pygame.mixer.music.play()


def stop_music():
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
