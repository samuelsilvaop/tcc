# midi_game/midi_warning.py
import pygame
import pygame.freetype

from midi_game.fonts import safe_text

BG = (0, 0, 0)
FG = (230, 230, 230)
WARN = (255, 180, 50)
DIM = (160, 160, 160)


def _center(screen, font, text, y, color):
    text = safe_text(text)
    rect = font.get_rect(text)
    x = (screen.get_width() - rect.width) // 2
    font.render_to(screen, (x, y), text, color)


def show_no_midi_screen(graphics):
    """
    Tela bloqueante:
    ENTER tenta de novo
    ESC volta pro menu
    """
    screen = graphics.screen
    clock = graphics.clock
    H = graphics.screen_height

    pygame.freetype.init()
    title_font = pygame.freetype.SysFont(None, int(H * 0.07))
    body_font = pygame.freetype.SysFont(None, int(H * 0.038))
    hint_font = pygame.freetype.SysFont(None, int(H * 0.03))

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return "menu"
                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return "retry"

        screen.fill(BG)
        _center(screen, title_font, "⚠️ Teclado MIDI não detectado", int(H * 0.30), WARN)
        _center(
            screen,
            body_font,
            "Conecte seu teclado MIDI via USB e aguarde o sistema reconhecer.",
            int(H * 0.44),
            FG,
        )
        _center(
            screen,
            hint_font,
            "ENTER = tentar novamente   •   ESC = voltar ao menu",
            int(H * 0.60),
            DIM,
        )

        pygame.display.flip()
        clock.tick(60)
