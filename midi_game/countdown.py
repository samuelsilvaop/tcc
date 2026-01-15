# midi_game/countdown.py
import time

import pygame
import pygame.freetype

BG = (0, 0, 0)
FG = (230, 230, 230)
HILITE = (70, 170, 255)


def _center_text(screen, font, text, y, color):
    rect = font.get_rect(text)
    x = (screen.get_width() - rect.width) // 2
    font.render_to(screen, (x, y), text, color)


def show_countdown(graphics, seconds=3):
    """
    Mostra 'Prepare-se...' e depois faz contagem 3..1 centralizada.
    Retorna False se o usuário sair, True caso contrário.
    """
    screen = graphics.screen
    clock = graphics.clock
    W, H = graphics.screen_width, graphics.screen_height

    pygame.freetype.init()
    title_font = pygame.freetype.SysFont(None, int(H * 0.09))
    big_font = pygame.freetype.SysFont(None, int(H * 0.20))
    hint_font = pygame.freetype.SysFont(None, int(H * 0.035))

    # Tela "Prepare-se..."
    t0 = time.time()
    while time.time() - t0 < 0.8:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return False

        screen.fill(BG)
        _center_text(screen, title_font, "Prepare-se...", int(H * 0.38), FG)
        _center_text(
            screen,
            hint_font,
            "A música vai começar em instantes",
            int(H * 0.55),
            HILITE,
        )
        pygame.display.flip()
        clock.tick(60)

    # Contagem 3..1
    for n in range(seconds, 0, -1):
        t1 = time.time()
        while time.time() - t1 < 1.0:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return False
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    return False

            screen.fill(BG)
            _center_text(screen, big_font, str(n), int(H * 0.33), HILITE)
            _center_text(screen, hint_font, "Segure-se! 🎹", int(H * 0.60), FG)
            pygame.display.flip()
            clock.tick(60)

    return True
