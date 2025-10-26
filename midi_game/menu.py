# midi_game/menu.py
import pygame
import pygame.freetype

from midi_game.midi_loader import list_midi_files

HILITE = (70, 170, 255)
FG = (230, 230, 230)
BG = (8, 8, 8)
DIM = (160, 160, 160)


def _draw_centered_text(screen, font, text, y, color):
    rect = font.get_rect(text)
    x = (screen.get_width() - rect.width) // 2
    font.render_to(screen, (x, y), text, color)


def _vertical_menu(graphics, title, options, selected_idx=0):
    """Desenha um menu vertical simples. Retorna o índice selecionado ou None (ESC)."""
    screen = graphics.screen
    clock = graphics.clock
    W, H = graphics.screen_width, graphics.screen_height

    pygame.freetype.init()
    title_font = pygame.freetype.SysFont(None, int(H * 0.07))
    item_font = pygame.freetype.SysFont(None, int(H * 0.04))

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

        _draw_centered_text(
            screen,
            item_font,
            "↑/↓ Navegar  •  ENTER Selecionar  •  ESC Voltar",
            int(H * 0.85),
            DIM,
        )

        pygame.display.flip()
        clock.tick(60)


def _music_picker(graphics):
    """Menu para escolher uma música .mid da pasta assets/midi."""
    files = list_midi_files()
    if not files:
        return None
    idx = _vertical_menu(graphics, "Selecionar música", files, selected_idx=0)
    return files[idx] if idx is not None else None


def _settings_placeholder(graphics):
    """Tela simples de 'Ajustes' (placeholder). Volta com ESC ou ENTER."""
    screen = graphics.screen
    clock = graphics.clock
    W, H = graphics.screen_width, graphics.screen_height

    pygame.freetype.init()
    t_font = pygame.freetype.SysFont(None, int(H * 0.06))
    s_font = pygame.freetype.SysFont(None, int(H * 0.035))

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.KEYDOWN and e.key in (
                pygame.K_ESCAPE,
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
            ):
                return

        screen.fill(BG)
        _draw_centered_text(screen, t_font, "Ajustes", int(H * 0.25), FG)
        _draw_centered_text(
            screen,
            s_font,
            "Em breve: número de teclas, nota mais grave, porta MIDI…",
            int(H * 0.45),
            FG,
        )
        _draw_centered_text(
            screen, s_font, "Pressione ESC para voltar", int(H * 0.75), DIM
        )
        pygame.display.flip()
        clock.tick(60)


def run_menu(graphics):
    """
    Exibe o menu principal e retorna um dict:
      {"action": "start", "midi": "fairy_tale.mid"}     -> iniciar com a padrão
      {"action": "start", "midi": "<arquivo>.mid"}      -> iniciar com a escolhida
      {"action": "quit"}                                -> sair
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
            # se cancelar, volta ao menu principal
            continue

        if options[choice] == "Ajustes":
            _settings_placeholder(graphics)
            continue

        if options[choice] == "Sair":
            return {"action": "quit"}
