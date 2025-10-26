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
