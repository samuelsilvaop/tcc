import json
import os

CONFIG_PATH = "midi_game/config.json"

DEFAULT_CONFIG = {"keyboard_keys": 49, "midi_port": None}


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
