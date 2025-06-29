import mido

from midi_game.config import load_config


def list_midi_ports():
    return mido.get_input_names()


def open_midi_port():
    config = load_config()
    port_name = config.get("midi_port")

    if not port_name or port_name not in list_midi_ports():
        raise Exception(f"Porta MIDI '{port_name}' inválida ou não encontrada.")

    return mido.open_input(port_name)
