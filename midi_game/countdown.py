# midi_game/countdown.py
import time

import pygame
import pygame.freetype


def show_countdown(graphics):
    """
    Exibe a tela de contagem regressiva (Prepare-se, 3, 2, 1).
    Dura exatamente 3 segundos no total.
    """
    screen = graphics.screen
    clock = graphics.clock
    W, H = graphics.screen_width, graphics.screen_height

    pygame.freetype.init()
    title_font = pygame.freetype.SysFont(None, int(H * 0.08))
    number_font = pygame.freetype.SysFont(None, int(H * 0.25))

    # Tela inicial "Prepare-se"
    screen.fill((0, 0, 0))
    title_font.render_to(
        screen, (W // 2 - 150, H // 2 - 50), "Prepare-se...", (255, 255, 255)
    )
    pygame.display.flip()
    time.sleep(0.8)

    # Contagem regressiva 3 → 2 → 1
    for n in [3, 2, 1]:
        screen.fill((0, 0, 0))
        text = str(n)
        rect = number_font.get_rect(text)
        number_font.render_to(
            screen,
            ((W - rect.width) // 2, (H - rect.height) // 2),
            text,
            (255, 255, 255),
        )
        pygame.display.flip()
        time.sleep(1)

    # Limpa a tela no final da contagem
    screen.fill((0, 0, 0))
    pygame.display.flip()
    time.sleep(0.3)
