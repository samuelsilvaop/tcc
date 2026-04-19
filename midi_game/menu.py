# midi_game/menu.py
from __future__ import annotations

import pygame
import pygame.freetype

from midi_game.config import (
    load_config,
    set_keyboard_keys,
    set_live_keyboard_sound,
    set_live_volume,
    set_lowest_note,
    set_midi_port,
    set_music_enabled,
    set_music_volume,
)
from midi_game.fonts import get_font
from midi_game.midi_input import list_midi_ports
from midi_game.midi_loader import list_midi_files

HILITE = (70, 170, 255)
FG = (230, 230, 230)
BG = (8, 8, 8)
DIM = (160, 160, 160)


def _draw_centered_text(screen, font, text, y, color):
    rect = font.get_rect(text)
    x = (screen.get_width() - rect.width) // 2
    font.render_to(screen, (x, y), text, color)


def _onoff(flag: bool) -> str:
    return "ON" if flag else "OFF"


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _adjust_volume(graphics, title: str, current: float):
    """
    Tela simples para ajustar volume [0..1] com ←/→ em passos de 0.05.
    ENTER confirma, ESC cancela (retorna None).
    """
    import pygame
    import pygame.freetype

    screen, clock = graphics.screen, graphics.clock
    W, H = graphics.screen_width, graphics.screen_height
    pygame.freetype.init()
    title_font = get_font(int(H * 0.06), bold=True)
    val_font = get_font(int(H * 0.10), bold=True)
    hint_font = get_font(int(H * 0.03), bold=True)

    vol = _clamp01(current)

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return None
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return None
                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return vol
                if e.key in (pygame.K_LEFT, pygame.K_a):
                    vol = _clamp01(vol - 0.05)
                if e.key in (pygame.K_RIGHT, pygame.K_d):
                    vol = _clamp01(vol + 0.05)

        screen.fill((8, 8, 8))
        _draw_centered_text(screen, title_font, title, int(H * 0.25), (230, 230, 230))
        _draw_centered_text(
            screen, val_font, f"{int(vol*100)}%", int(H * 0.45), (70, 170, 255)
        )
        _draw_centered_text(
            screen,
            hint_font,
            "←/→ ajustar   •   ENTER confirmar   •   ESC cancelar",
            int(H * 0.80),
            (160, 160, 160),
        )
        pygame.display.flip()
        clock.tick(60)


def _vertical_menu(
    graphics,
    title,
    options,
    selected_idx=0,
    footer_hint="↑/↓ Navegar  •  ENTER Selecionar  •  ESC Voltar",
):
    """Desenha um menu vertical simples. Retorna o índice selecionado ou None (ESC/fechar)."""
    screen = graphics.screen
    clock = graphics.clock
    W, H = graphics.screen_width, graphics.screen_height

    pygame.freetype.init()
    title_font = get_font(int(H * 0.07), bold=True)
    item_font = get_font(int(H * 0.04), bold=True)
    foot_font = get_font(int(H * 0.03), bold=True)

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return None
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return None
                if e.key in (pygame.K_UP, pygame.K_w):
                    selected_idx = (selected_idx - 1) % len(options)
                if e.key in (pygame.K_DOWN, pygame.K_s):
                    selected_idx = (selected_idx + 1) % len(options)
                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return selected_idx

        screen.fill(BG)
        _draw_centered_text(screen, title_font, title, int(H * 0.18), FG)

        base_y = int(H * 0.35)
        line_h = int(H * 0.065)

        for i, label in enumerate(options):
            color = HILITE if i == selected_idx else FG
            _draw_centered_text(screen, item_font, label, base_y + i * line_h, color)

        _draw_centered_text(screen, foot_font, footer_hint, int(H * 0.85), DIM)

        pygame.display.flip()
        clock.tick(60)


def _music_picker(graphics):
    files = list_midi_files()
    if not files:
        return None
    idx = _vertical_menu(graphics, "Selecionar música", files, selected_idx=0)
    return files[idx] if idx is not None else None


# ---------- AJUSTES ----------
def _pick_keyboard_keys(graphics):
    options = ["49", "61", "76", "88"]
    idx = 1  # default visual em 61
    choice = _vertical_menu(graphics, "Número de teclas", options, idx)
    if choice is None:
        return None
    return int(options[choice])


def _note_name(n):
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return f"{names[n % 12]}{n // 12 - 1}"


def _pick_lowest_note(graphics):
    """
    Presets comuns + ajuste fino:
    ←/→ alterna presets, PageUp/PageDown ajusta ±1 semitom.
    ENTER confirma, ESC cancela.
    """
    screen = graphics.screen
    clock = graphics.clock
    W, H = graphics.screen_width, graphics.screen_height

    pygame.freetype.init()
    title_font = get_font(int(H * 0.065), bold=True)
    val_font = get_font(int(H * 0.06), bold=True)
    hint_font = get_font(int(H * 0.03), bold=True)

    presets = [21, 33, 36, 48]  # A0, A1, C2, C3 – comuns em 49/61/76/88
    idx = 2  # C2 como default
    current = presets[idx]

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return None
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return None
                if e.key in (pygame.K_LEFT, pygame.K_a):
                    idx = (idx - 1) % len(presets)
                    current = presets[idx]
                if e.key in (pygame.K_RIGHT, pygame.K_d):
                    idx = (idx + 1) % len(presets)
                    current = presets[idx]
                if e.key == pygame.K_PAGEUP:
                    current += 1
                if e.key == pygame.K_PAGEDOWN:
                    current -= 1
                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return max(0, min(127, current))

        screen.fill(BG)
        _draw_centered_text(
            screen, title_font, "Nota mais grave (lowest_note)", int(H * 0.22), FG
        )
        _draw_centered_text(
            screen,
            val_font,
            f"{_note_name(current)}  (MIDI {current})",
            int(H * 0.42),
            HILITE,
        )
        _draw_centered_text(
            screen,
            hint_font,
            "←/→ presets   •   PgUp/PgDn ±1 semitom   •   ENTER confirmar   •   ESC voltar",
            int(H * 0.8),
            DIM,
        )

        pygame.display.flip()
        clock.tick(60)


def _pick_midi_port(graphics):
    ports = list_midi_ports()
    if not ports:
        _vertical_menu(
            graphics,
            "Portas MIDI",
            ["Nenhuma porta encontrada"],
            0,
            footer_hint="ESC para voltar",
        )
        return None
    idx = _vertical_menu(graphics, "Escolher porta MIDI", ports, selected_idx=0)
    return ports[idx] if idx is not None else None


def _settings_screen(graphics):
    """
    Tela de ajustes com:
      - Número de teclas (49/61/76/88)
      - Nota mais grave (lowest_note)
      - Porta MIDI
      - Som do teclado ao vivo (ON/OFF)
      - Música da faixa (ON/OFF)
      - Voltar
    Cada confirmação salva no config.json.
    """
    cfg = load_config()

    def summary():
        c = load_config()
        return [
            f"Número de teclas: {c.get('keyboard_keys', 61)}",
            f"Nota mais grave: {_note_name(c.get('lowest_note', 36))} (MIDI {c.get('lowest_note', 36)})",
            f"Porta MIDI: {c.get('midi_port') or '— não definida —'}",
            f"Som do teclado ao vivo: {_onoff(c.get('live_keyboard_sound', False))}",
            f"Música da faixa: {_onoff(c.get('music_enabled', True))}",
            f"Volume música: {int(c.get('music_volume', 0.7)*100)}%",  # novo
            f"Volume teclado: {int(c.get('live_volume', 0.5)*100)}%",  # novo
            "Voltar",
        ]

    selected = 0
    while True:
        opts = summary()
        choice = _vertical_menu(graphics, "Ajustes", opts, selected_idx=selected)
        if choice is None or opts[choice] == "Voltar":
            return

        selected = choice

        if choice == 0:  # número de teclas
            v = _pick_keyboard_keys(graphics)
            if v is not None:
                set_keyboard_keys(v)

        elif choice == 1:  # lowest_note
            v = _pick_lowest_note(graphics)
            if v is not None:
                set_lowest_note(v)

        elif choice == 2:  # porta MIDI
            v = _pick_midi_port(graphics)
            if v:
                set_midi_port(v)

        elif choice == 3:  # toggle live on/off
            cur = load_config().get("live_keyboard_sound", False)
            set_live_keyboard_sound(not cur)

        elif choice == 4:  # toggle music on/off
            cur = load_config().get("music_enabled", True)
            set_music_enabled(not cur)

        elif choice == 5:  # Volume música
            cur = load_config().get("music_volume", 0.7)
            v = _adjust_volume(graphics, "Volume da música", cur)
            if v is not None:
                set_music_volume(v)

        elif choice == 6:  # Volume teclado
            cur = load_config().get("live_volume", 0.5)
            v = _adjust_volume(graphics, "Volume do teclado ao vivo", cur)
            if v is not None:
                set_live_volume(v)


def run_menu(graphics):
    """
    Exibe o menu principal e retorna um dict:
      {"action": "start", "midi": "fairy_tale.mid"}
      {"action": "start", "midi": "<arquivo>.mid"}
      {"action": "quit"}
    """
    options = [
        "Iniciar (fairy_tale.mid)",
        "Selecionar música",
        "Ajustes",
        "Sair",
    ]
    selected = 0

    while True:
        choice = _vertical_menu(graphics, "MIDI Hero", options, selected_idx=selected)
        if choice is None:
            return {"action": "quit"}

        selected = choice

        if options[choice].startswith("Iniciar"):
            return {"action": "start", "midi": "fairy_tale.mid"}

        if options[choice] == "Selecionar música":
            pick = _music_picker(graphics)
            if pick:
                return {"action": "start", "midi": pick}
            continue

        if options[choice] == "Ajustes":
            _settings_screen(graphics)
            continue

        if options[choice] == "Sair":
            return {"action": "quit"}
