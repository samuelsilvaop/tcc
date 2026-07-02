# midi_game/midi_input.py
from __future__ import annotations

import mido
from midi_game.config import load_config

# nomes comuns de portas "falsas"/do sistema (Linux/Windows/mac)
BAD_PORT_HINTS = [
    "midi through",
    "through port",
    "rtmidi",
    "system",
    "mapper",
    "loop",
    "virtual",
    "monitor",
]


def list_midi_ports():
    return mido.get_input_names()


def _is_real_port(name: str) -> bool:
    n = (name or "").strip().lower()
    if not n:
        return False
    return not any(h in n for h in BAD_PORT_HINTS)


def pick_best_port(preferred_name: str | None):
    """
    Retorna:
      (port_name, is_real)
    onde is_real=True só se a porta não for "Midi Through"/virtual.
    """
    ports = list_midi_ports()
    if not ports:
        return None, False

    # 1) tenta porta do config
    if preferred_name and preferred_name in ports and _is_real_port(preferred_name):
        return preferred_name, True

    # 2) pega primeira porta REAL disponível
    real_ports = [p for p in ports if _is_real_port(p)]
    if real_ports:
        return real_ports[0], True

    # 3) só sobrou porta virtual (ex: Midi Through)
    return ports[0], False


def open_midi_port():
    """
    Abre uma porta MIDI REAL se existir.
    Se não existir (só virtual), retorna (None, False).
    """
    cfg = load_config()
    preferred = cfg.get("midi_port")

    port_name, is_real = pick_best_port(preferred)
    if not port_name:
        return None, False

    if not is_real:
        # não abre "Midi Through" como se fosse teclado real
        return None, False

    try:
        port = mido.open_input(port_name)
        return port, True
    except Exception as e:
        print(f"[AVISO] Falha ao abrir porta MIDI '{port_name}': {e}")
        return None, False
