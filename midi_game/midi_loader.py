import os

import mido

MIDI_FOLDER = "midi_game/assets/midi"


def list_midi_files():
    """Lista arquivos .mid na pasta de músicas."""
    return [f for f in os.listdir(MIDI_FOLDER) if f.lower().endswith(".mid")]


def load_midi_file(filename: str):
    """Carrega e processa o arquivo MIDI em uma lista de eventos com tempo acumulado (segundos)."""
    path = os.path.join(MIDI_FOLDER, filename)
    mid = mido.MidiFile(path)

    events = []
    current_time = 0.0

    for msg in mid:
        current_time += float(msg.time)
        if msg.type in ["note_on", "note_off"]:
            events.append(
                {
                    "time": current_time,
                    "type": msg.type,
                    "note": msg.note,
                    "velocity": getattr(msg, "velocity", 0),
                }
            )

    return events


def build_note_spans(events: list[dict]):
    """
    Recebe a lista de eventos (note_on/note_off com 'time' acumulado)
    e retorna spans com início/fim por nota:
      {"note": 60, "start": 1.23, "end": 2.10, "duration": 0.87}

    Suporta sobreposição da mesma nota (pilha).
    """
    spans = []
    stacks: dict[int, list[float]] = {}  # note -> [start_times]

    for e in events:
        t = float(e["time"])
        note = int(e["note"])
        etype = e["type"]
        vel = int(e.get("velocity", 0))

        if etype == "note_on" and vel > 0:
            stacks.setdefault(note, []).append(t)

        elif etype == "note_off" or (etype == "note_on" and vel == 0):
            stk = stacks.get(note)
            if stk:
                start = stk.pop()
                if t > start:
                    spans.append(
                        {"note": note, "start": start, "end": t, "duration": t - start}
                    )

    # Se alguma tecla ficou aberta sem note_off, cria span até o fim do último evento
    last_time = float(events[-1]["time"]) if events else 0.0
    for note, stk in stacks.items():
        for start in stk:
            end = max(start + 0.05, last_time)  # barra mínima
            spans.append(
                {"note": note, "start": start, "end": end, "duration": end - start}
            )

    # opcional: ordenar por inicio (ajuda visualmente)
    spans.sort(key=lambda s: (s["start"], s["note"]))
    return spans


def load_midi_note_spans(filename: str):
    """
    ✅ API pública esperada por alguns engines:
    devolve diretamente os spans de notas do arquivo MIDI.
    """
    events = load_midi_file(filename)
    return build_note_spans(events)
