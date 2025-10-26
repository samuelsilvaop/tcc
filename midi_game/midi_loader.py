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


def build_note_spans(events):
    """
    Recebe a lista de eventos (note_on/note_off com 'time' acumulado)
    e retorna spans com início/fim por nota:
      {"note": 60, "start": 1.23, "end": 2.10, "duration": 0.87}
    Suporta sobreposição da mesma nota (pilha).
    """
    spans = []
    stacks = {}  # note -> [start_times]

    for e in events:
        t = e["time"]
        if e["type"] == "note_on" and e["velocity"] > 0:
            stacks.setdefault(e["note"], []).append(t)
        elif e["type"] in ("note_off", "note_on") and (
            e["type"] == "note_off" or e["velocity"] == 0
        ):
            stk = stacks.get(e["note"])
            if stk:
                start = stk.pop()  # último começo aberto
                if t > start:
                    spans.append(
                        {
                            "note": e["note"],
                            "start": start,
                            "end": t,
                            "duration": t - start,
                        }
                    )
    # Se alguma tecla ficou aberta sem note_off, cria span até o fim do último evento
    last_time = events[-1]["time"] if events else 0.0
    for note, stk in stacks.items():
        for start in stk:
            end = max(start + 0.05, last_time)  # barra mínima
            spans.append(
                {"note": note, "start": start, "end": end, "duration": end - start}
            )
    return spans
