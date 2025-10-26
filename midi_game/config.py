import json
import os

CONFIG_PATH = "midi_game/config.json"


DEFAULT_CONFIG = {
    "keyboard_keys": 61,
    "midi_port": None,
    "lowest_note": 36,
    "live_keyboard_sound": False,
    "music_enabled": True,
    "music_volume": 0.7,  # novo (0.0–1.0)
    "live_volume": 0.5,  # novo (0.0–1.0)
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)


def set_keyboard_keys(n):
    config = load_config()
    config["keyboard_keys"] = n
    save_config(config)


def set_midi_port(port_name):
    config = load_config()
    config["midi_port"] = port_name
    save_config(config)


def set_lowest_note(note_number: int):
    config = load_config()
    config["lowest_note"] = int(note_number)
    save_config(config)


def set_live_keyboard_sound(flag: bool):
    cfg = load_config()
    cfg["live_keyboard_sound"] = bool(flag)
    save_config(cfg)


def set_music_enabled(flag: bool):
    cfg = load_config()
    cfg["music_enabled"] = bool(flag)
    save_config(cfg)


def set_music_volume(v: float):
    cfg = load_config()
    cfg["music_volume"] = max(0.0, min(1.0, float(v)))
    save_config(cfg)


def set_live_volume(v: float):
    cfg = load_config()
    cfg["live_volume"] = max(0.0, min(1.0, float(v)))
    save_config(cfg)
