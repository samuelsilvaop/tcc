from __future__ import annotations

import json
import os
from pathlib import Path

SAVE_DATA_PATH = Path(__file__).parent / "save_data.json"


def load_save_data() -> dict:
    if not os.path.exists(SAVE_DATA_PATH):
        return {}
    try:
        with open(SAVE_DATA_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # mesmo raciocínio do config.py: não travar o jogo por causa de um
        # save_data.json corrompido, só perde os recordes salvos.
        print(
            f"[AVISO] {SAVE_DATA_PATH} corrompido ou ilegivel; ignorando recordes salvos."
        )
        return {}


def _save(data: dict):
    tmp_path = f"{SAVE_DATA_PATH}.tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=4)
    os.replace(tmp_path, SAVE_DATA_PATH)


def register_score(song_name: str, score: int, max_score: int) -> tuple[int, bool]:
    """Registra o score da tentativa e atualiza o recorde da música se superado.

    Retorna (melhor_score, é_novo_recorde).
    """
    data = load_save_data()
    entry = data.get(song_name)
    is_new_record = entry is None or int(score) > int(entry.get("best_score", 0))

    if is_new_record:
        data[song_name] = {"best_score": int(score), "max_score": int(max_score)}
        _save(data)
        return int(score), True

    return int(entry["best_score"]), False
