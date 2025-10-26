# midi_game/splash.py
import pygame
import pygame.freetype


def show_splash(graphics) -> bool:
    """
    Exibe a tela 'desenvolvido por Samuel Silva' por exatamente 2 segundos.
    Retorna False se o usuário fechar/ESC durante a splash; True caso contrário.
    """
    screen = graphics.screen
    clock = graphics.clock
    W, H = graphics.screen_width, graphics.screen_height

    # fontes
    pygame.freetype.init()
    credit_font = pygame.freetype.SysFont(None, int(H * 0.045))
    sub_font = pygame.freetype.SysFont(None, int(H * 0.028))

    text_main = "desenvolvido por Samuel Silva"
    text_sub = "MIDI Hero"

    start_ms = pygame.time.get_ticks()
    duration_ms = 2000  # 2.000 ms = 2s exatos

    while True:
        # eventos (permitir sair com ESC/fechar janela)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return False

        elapsed = pygame.time.get_ticks() - start_ms
        if elapsed >= duration_ms:
            return True

        # desenha
        screen.fill((0, 0, 0))

        # centraliza textos
        main_rect = credit_font.get_rect(text_main)
        main_x = (W - main_rect.width) // 2
        main_y = (H - main_rect.height) // 2
        credit_font.render_to(screen, (main_x, main_y), text_main, (255, 255, 255))

        sub_rect = sub_font.get_rect(text_sub)
        sub_x = (W - sub_rect.width) // 2
        sub_y = main_y + main_rect.height + int(H * 0.02)
        sub_font.render_to(screen, (sub_x, sub_y), text_sub, (200, 200, 200))

        pygame.display.flip()
        clock.tick(60)
