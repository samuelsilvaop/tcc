# midi_game/menu.py
import pygame
import pygame.freetype


def run_menu(graphics) -> str:
    """
    Mostra um menu simples após a splash.
    Retorna "start" quando o usuário pressionar ENTER.
    Retorna "quit" se fechar/ESC.
    """
    screen = graphics.screen
    clock = graphics.clock
    W, H = graphics.screen_width, graphics.screen_height

    pygame.freetype.init()
    title_font = pygame.freetype.SysFont(None, int(H * 0.07))
    hint_font = pygame.freetype.SysFont(None, int(H * 0.032))

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return "quit"
                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return "start"

        screen.fill((8, 8, 8))

        title = "MIDI Hero"
        hint = "Pressione ENTER para iniciar"

        t_rect = title_font.get_rect(title)
        h_rect = hint_font.get_rect(hint)

        t_x = (W - t_rect.width) // 2
        t_y = int(H * 0.33)
        h_x = (W - h_rect.width) // 2
        h_y = t_y + t_rect.height + int(H * 0.04)

        title_font.render_to(screen, (t_x, t_y), title, (255, 255, 255))
        hint_font.render_to(screen, (h_x, h_y), hint, (180, 180, 180))

        pygame.display.flip()
        clock.tick(60)
