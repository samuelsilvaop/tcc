import mido

from midi_game.config import load_config


def list_midi_ports():
    return mido.get_input_names()


def open_midi_port(preferred: str | None = None, auto_pick: bool = True):
    names = list_midi_ports()
    if not names:
        raise Exception("Nenhuma porta MIDI de entrada encontrada.")

    # 0) Prioridade: config (nome exato ou substring)
    config = load_config()
    cfg = (config.get("midi_port") or "").strip()

    if cfg:
        # se bater exato
        if cfg in names:
            print(f"🎹 Abrindo porta MIDI (config exata): {cfg}")
            return mido.open_input(cfg)

        # se bater por substring
        for n in names:
            if cfg.lower() in n.lower():
                print(f"🎹 Abrindo porta MIDI (config ~): {n}")
                return mido.open_input(n)

        print(f"⚠️ Porta do config não encontrada: {cfg}")

    # 1) Se foi passado um preferred (ex: "AK490"), tenta casar por substring
    if preferred:
        for n in names:
            if preferred.lower() in n.lower():
                print(f"🎹 Abrindo porta MIDI (preferred): {n}")
                return mido.open_input(n)

    # 2) Se só existe 1 porta, abre ela
    if len(names) == 1:
        print(f"🎹 Abrindo única porta MIDI disponível: {names[0]}")
        return mido.open_input(names[0])

    # 3) Auto-pick (evita portas “fake” tipo Midi Through/System)
    if auto_pick:
        blacklist = ("through", "announce", "system", "timer")
        candidates = [n for n in names if not any(b in n.lower() for b in blacklist)]
        pick = candidates[0] if candidates else names[0]
        print(f"🎹 Abrindo porta MIDI (auto-pick): {pick}")
        return mido.open_input(pick)

    # 4) Se chegou aqui, exige escolha manual
    print("Portas MIDI disponíveis:")
    for i, n in enumerate(names):
        print(f"{i}: {n}")
    raise Exception("Múltiplas portas MIDI encontradas. Defina midi_port no config.")
