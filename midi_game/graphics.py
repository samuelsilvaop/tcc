import pygame
import pygame.freetype

from midi_game.config import load_config

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (66, 135, 245)
GREEN = (50, 200, 100)
RED = (255, 50, 50)

NOTE_HEIGHT = 20
FPS = 60

WHITE_KEY_HEIGHT = int(60 * 3.95)
BLACK_KEY_HEIGHT = int(40 * 3.95)


class Graphics:
    def __init__(self):
        pygame.init()
        pygame.freetype.init()
        self.font = pygame.freetype.SysFont(None, 14)  # levemente maior

        info = pygame.display.Info()
        self.screen = pygame.display.set_mode(
            (info.current_w, info.current_h), pygame.FULLSCREEN
        )
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        pygame.display.set_caption("MIDI Hero")

        self.clock = pygame.time.Clock()
        self.config = load_config()
        self.scroll_speed = 140  # pixels por segundo (ajuste fino)
        # pré-calcula geometria das teclas (brancas e pretas) para mapear X corretamente
        white_note_offsets = [0, 2, 4, 5, 7, 9, 11]
        self.white_notes = [
            n
            for n in range(self.lowest_note, self.lowest_note + self.num_keys)
            if n % 12 in white_note_offsets
        ]
        self.white_key_width = self.screen_width // len(self.white_notes)
        self.black_key_width = self.white_key_width * 0.6

        self.num_keys = self.config["keyboard_keys"]
        self.lowest_note = self.config.get("lowest_note", 36)
        self.key_width = self.screen_width // self.num_keys

    def note_name(self, note_number):
        names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        name = names[note_number % 12]
        octave = note_number // 12 - 1
        return f"{name}{octave}"

    def draw_keyboard(self, pressed_notes=None):
        if pressed_notes is None:
            pressed_notes = []

        white_note_offsets = [0, 2, 4, 5, 7, 9, 11]
        white_notes = [
            n
            for n in range(self.lowest_note, self.lowest_note + self.num_keys)
            if n % 12 in white_note_offsets
        ]

        white_key_width = self.screen_width // len(white_notes)

        # Desenha teclas brancas
        for i, note in enumerate(white_notes):
            x = i * white_key_width
            color = GREEN if note in pressed_notes else WHITE
            pygame.draw.rect(
                self.screen,
                color,
                (
                    x,
                    self.screen_height - WHITE_KEY_HEIGHT,
                    white_key_width,
                    WHITE_KEY_HEIGHT,
                ),
            )
            pygame.draw.rect(
                self.screen,
                BLACK,
                (
                    x,
                    self.screen_height - WHITE_KEY_HEIGHT,
                    white_key_width,
                    WHITE_KEY_HEIGHT,
                ),
                1,
            )

            note_name = self.note_name(note)
            self.font.render_to(
                self.screen, (x + 4, self.screen_height - 20), note_name, BLACK
            )

        # Desenha teclas pretas
        black_key_width = white_key_width * 0.6

        for i in range(len(white_notes) - 1):
            note = white_notes[i]
            black_note = note + 1
            if black_note % 12 in [1, 3, 6, 8, 10]:
                x = (i + 1) * white_key_width - (black_key_width / 2)
                color = RED if black_note in pressed_notes else BLACK
                pygame.draw.rect(
                    self.screen,
                    color,
                    (
                        x,
                        self.screen_height - WHITE_KEY_HEIGHT,
                        black_key_width,
                        BLACK_KEY_HEIGHT,
                    ),
                )

                note_name = self.note_name(black_note)
                self.font.render_to(
                    self.screen,
                    (x + 2, self.screen_height - WHITE_KEY_HEIGHT + 10),
                    note_name,
                    WHITE,
                )

    def draw_notes(self, active_notes, current_time):
        for note_event in active_notes:
            note = note_event["note"]
            time_diff = note_event["time"] - current_time
            y = self.screen_height - WHITE_KEY_HEIGHT - (time_diff * 100)
            x = (note - self.lowest_note) * self.key_width
            if 0 <= x <= self.screen_width and 0 <= y <= self.screen_height:
                pygame.draw.rect(self.screen, BLUE, (x, y, self.key_width, NOTE_HEIGHT))

    def update(self, active_notes, current_time, pressed_notes):
        self.screen.fill(BLACK)
        self.draw_notes(active_notes, current_time)
        self.draw_keyboard(pressed_notes)
        pygame.display.flip()
        self.clock.tick(FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
        return True

    def quit(self):
        pygame.quit()

    def note_to_xw(self, note):
        """
        Retorna (x, width, is_black) alinhado com o teclado já desenhado.
        """
        is_black = (note % 12) in (1, 3, 6, 8, 10)
        if not is_black:
            # índice da nota dentro das brancas
            try:
                idx = self.white_notes.index(note)
            except ValueError:
                # se a nota não for branca no range, aproxima pela vizinha
                # (não deve acontecer se lowest_note/num_keys cobrem o teclado)
                idx = 0
            x = idx * self.white_key_width
            return x, self.white_key_width, False
        else:
            # preta fica entre duas brancas: C -> C# antes de D, etc.
            # encontre a branca imediatamente anterior (note-1)
            left_white = note - 1
            # posição de onde a preta fica: no "lado direito" da branca à esquerda
            try:
                idx = self.white_notes.index(left_white)
                x = (idx + 1) * self.white_key_width - (self.black_key_width / 2)
            except ValueError:
                # fallback: encosta na borda esquerda
                x = 0
            return x, self.black_key_width, True

    def draw_note_bars_upwards(self, spans, current_time):
        """
        Para cada span:
        - base (linha de acerto) é imediatamente acima do teclado branco
        - y_base sobe conforme o momento de início se aproxima
        - altura = duração * velocidade
        """
        hit_line_y = self.screen_height - WHITE_KEY_HEIGHT  # linha de acerto
        for s in spans:
            start = s["start"]
            end = s["end"]
            duration = max(0.05, end - start)

            # tempo até o início chegar na linha de acerto
            time_to_start = (
                start - current_time
            )  # se >0 ainda vai chegar; se <0 já começou
            y_base = hit_line_y - (time_to_start * self.scroll_speed)
            height = duration * self.scroll_speed
            y_top = y_base - height

            x, w, is_black = self.note_to_xw(s["note"])

            # culling simples (fora de tela)
            if y_top > self.screen_height or y_base < 0:
                continue

            # cor: usa BLUE para barras; você pode diferenciar pretas/brancas se quiser
            pygame.draw.rect(self.screen, BLUE, (x, y_top, w, height))

    def update_bars(self, visible_spans, current_time, pressed_notes):
        self.screen.fill(BLACK)
        self.draw_note_bars_upwards(visible_spans, current_time)
        self.draw_keyboard(pressed_notes)
        pygame.display.flip()
        self.clock.tick(FPS)
