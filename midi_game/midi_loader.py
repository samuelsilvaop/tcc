import os

import mido

MIDI_FOLDER = "midi_game/assets/midi"


def list_midi_files():
    """Lista arquivos .mid na pasta de músicas."""
    return [f for f in os.listdir(MIDI_FOLDER) if f.lower().endswith(".mid")]


def load_midi_file(filename):
    """Carrega e processa o arquivo MIDI em uma lista de eventos."""
    path = os.path.join(MIDI_FOLDER, filename)
    mid = mido.MidiFile(path)

    events = []
    current_time = 0

    for msg in mid:
        current_time += msg.time
        if msg.type in ["note_on", "note_off"]:
            events.append(
                {
                    "time": current_time,
                    "type": msg.type,
                    "note": msg.note,
                    "velocity": msg.velocity,
                }
            )

    return events
