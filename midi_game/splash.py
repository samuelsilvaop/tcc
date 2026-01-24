# midi_game/splash.py
import pygame
import pygame.freetype

from midi_game.fonts import get_font


def show_splash(graphics) -> bool:
    """
    Exibe a tela de crédito por 1 segundo.
    Retorna False se ESC/fechar; True caso contrário.
    """

    screen = graphics.screen
    clock = graphics.clock

    # ✅ pega tamanho REAL da surface (funciona em qualquer monitor)
    W, H = screen.get_size()

    credit_font = get_font(int(H * 0.045))
    sub_font = get_font(int(H * 0.028))

    text_main = "desenvolvido por Samuel Silva"
    text_sub = "MIDI Hero"

    start_ms = pygame.time.get_ticks()
    duration_ms = 1000

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return False

        elapsed = pygame.time.get_ticks() - start_ms
        if elapsed >= duration_ms:
            return True

        screen.fill((0, 0, 0))

        # ✅ Centralização correta
        main_rect = credit_font.get_rect(text_main)
        main_x = (W - main_rect.width) // 2
        main_y = (H - main_rect.height) // 2

        credit_font.render_to(
            screen,
            (main_x, main_y),
            text_main,
            (255, 255, 255),
        )

        sub_rect = sub_font.get_rect(text_sub)
        sub_x = (W - sub_rect.width) // 2
        sub_y = main_y + main_rect.height + int(H * 0.02)

        sub_font.render_to(
            screen,
            (sub_x, sub_y),
            text_sub,
            (180, 180, 180),
        )

        pygame.display.flip()
        clock.tick(60)
