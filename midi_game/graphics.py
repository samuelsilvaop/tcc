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

WHITE_BAR_INSET_PX = 2
BLACK_BAR_INSET_PX = 2

BAR_OUTLINE_PX = 1
BAR_INNER_INSET = 3
BAR_SHADOW_OFFSET = (2, 2)
BAR_TOP_HIGHLIGHT_PX = 2
BAR_OUTER_INSET = 15


def _is_black(note: int) -> bool:
    return (note % 12) in (1, 3, 6, 8, 10)


def _clamp(v: int) -> int:
    return max(0, min(255, int(v)))


def _darken(color, amt: int):
    r, g, b = color
    return (_clamp(r - amt), _clamp(g - amt), _clamp(b - amt))


def _lighten(color, amt: int):
    r, g, b = color
    return (_clamp(r + amt), _clamp(g + amt), _clamp(b + amt))


class Graphics:
    def __init__(self):
        pygame.init()
        pygame.freetype.init()
        self.font = pygame.freetype.SysFont(None, 14)

        self.clock = pygame.time.Clock()
        self.config = load_config()

        # valores default (serão setados no refresh_display)
        self.screen = None
        self.screen_width = 0
        self.screen_height = 0

        self.num_keys = int(self.config["keyboard_keys"])
        self.lowest_note = int(self.config.get("lowest_note", 36))
        self.scroll_speed = 140

        # geometria (preenchida no refresh_display)
        self.WHITE_KEY_HEIGHT = 0
        self.BLACK_KEY_HEIGHT = 0
        self.white_notes = []
        self.white_key_x = []
        self.white_key_w = []
        self.note_xw = {}

        # cria display e calcula tudo
        self.refresh_display(force=True)

    def refresh_display(self, force: bool = False):
        """
        Recria fullscreen no tamanho do display atual e recalcula toda a geometria.
        Chame isso ao mudar de monitor/resolução.
        """
        info = pygame.display.Info()

        new_w = info.current_w
        new_h = info.current_h

        if (not force) and (new_w == self.screen_width and new_h == self.screen_height):
            return

        # ✅ recria a janela fullscreen pegando o monitor atual
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("MIDI Hero")

        self.screen_width = new_w
        self.screen_height = new_h

        # ✅ alturas agora são atributos (usados em todo o arquivo)
        self.WHITE_KEY_HEIGHT = int(self.screen_height * 0.28)
        self.BLACK_KEY_HEIGHT = int(self.WHITE_KEY_HEIGHT * 0.66)

        # ✅ recalcula layout das brancas
        white_notes = []
        for n in range(self.lowest_note, self.lowest_note + self.num_keys):
            if not _is_black(n):
                white_notes.append(n)

        nW = max(1, len(white_notes))
        edges = [round(i * self.screen_width / nW) for i in range(nW + 1)]
        self.white_key_x = edges[:-1]
        self.white_key_w = [edges[i + 1] - edges[i] for i in range(nW)]
        self.white_notes = white_notes

        # ✅ recalcula mapa nota -> (x,w,is_black)
        self.note_xw = {}
        w_idx = 0

        for n in range(self.lowest_note, self.lowest_note + self.num_keys):
            if not _is_black(n):
                x = self.white_key_x[w_idx] + WHITE_BAR_INSET_PX
                w = max(2, self.white_key_w[w_idx] - 2 * WHITE_BAR_INSET_PX)
                self.note_xw[n] = (x, w, False)
                w_idx += 1
            else:
                left_i = max(0, w_idx - 1)
                right_i = min(len(self.white_key_x) - 1, w_idx)

                border_x = self.white_key_x[left_i] + self.white_key_w[left_i]
                left_w = self.white_key_w[left_i]
                right_w = self.white_key_w[right_i]
                bw_raw = int(min(left_w, right_w) * 0.6)
                bw = max(6, bw_raw - 2 * BLACK_BAR_INSET_PX)

                x = border_x - (bw // 2) + BLACK_BAR_INSET_PX
                self.note_xw[n] = (x, bw, True)

    def note_name(self, note_number):
        names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        name = names[note_number % 12]
        octave = note_number // 12 - 1
        return f"{name}{octave}"

    def draw_keyboard(self, pressed_notes=None):
        if pressed_notes is None:
            pressed_notes = []

        # brancas
        for i, note in enumerate(self.white_notes):
            x = self.white_key_x[i]
            w = self.white_key_w[i]
            color = GREEN if note in pressed_notes else WHITE
            pygame.draw.rect(
                self.screen,
                color,
                (
                    x,
                    self.screen_height - self.WHITE_KEY_HEIGHT,
                    w,
                    self.WHITE_KEY_HEIGHT,
                ),
            )
            pygame.draw.rect(
                self.screen,
                BLACK,
                (
                    x,
                    self.screen_height - self.WHITE_KEY_HEIGHT,
                    w,
                    self.WHITE_KEY_HEIGHT,
                ),
                1,
            )
            self.font.render_to(
                self.screen,
                (x + 4, self.screen_height - 20),
                self.note_name(note),
                BLACK,
            )

        # pretas
        for i in range(len(self.white_notes) - 1):
            left_white = self.white_notes[i]
            black_note = left_white + 1
            if _is_black(black_note):
                xw = self.note_xw.get(black_note)
                if not xw:
                    continue
                x, bw, _ = xw
                color = RED if black_note in pressed_notes else BLACK
                pygame.draw.rect(
                    self.screen,
                    color,
                    (
                        x,
                        self.screen_height - self.WHITE_KEY_HEIGHT,
                        bw,
                        self.BLACK_KEY_HEIGHT,
                    ),
                )
                self.font.render_to(
                    self.screen,
                    (x + 2, self.screen_height - self.WHITE_KEY_HEIGHT + 10),
                    self.note_name(black_note),
                    WHITE,
                )

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

                # ✅ “reconhecer tela” manual (se quiser): F5 recalcula tudo
                if event.key == pygame.K_F5:
                    self.refresh_display(force=True)

        return True

    def quit(self):
        pygame.quit()

    def _draw_bar_fx(self, x: int, y: float, w: int, h: float, base_color):
        y = int(y)
        h = int(h)
        if h <= 0 or w <= 0:
            return

        outer = min(BAR_OUTER_INSET, max(0, (w - 4) // 2))
        x = x + outer
        w = w - 2 * outer
        if w <= 2:
            return

        sx, sy = BAR_SHADOW_OFFSET
        shadow_color = _darken(base_color, 120)
        pygame.draw.rect(self.screen, shadow_color, (x + sx, y + sy, w, h))

        pygame.draw.rect(self.screen, base_color, (x, y, w, h))

        outline_color = _darken(base_color, 90)
        pygame.draw.rect(self.screen, outline_color, (x, y, w, h), BAR_OUTLINE_PX)

        inner_x = x + BAR_INNER_INSET
        inner_w = w - 2 * BAR_INNER_INSET
        if inner_w > 2 and h > 6:
            inner_color = _lighten(base_color, 35)
            pygame.draw.rect(self.screen, inner_color, (inner_x, y + 2, inner_w, h - 4))

        highlight_color = _lighten(base_color, 70)
        pygame.draw.rect(
            self.screen, highlight_color, (x + 1, y + 1, w - 2, BAR_TOP_HIGHLIGHT_PX)
        )

    def draw_note_bars_upwards(self, spans, current_time):
        hit_line_y = self.screen_height - self.WHITE_KEY_HEIGHT

        for s in spans:
            start = s["start"]
            end = s["end"]
            dur = max(0.05, end - start)

            time_to_start = start - current_time
            y_base = hit_line_y - (time_to_start * self.scroll_speed)
            height = dur * self.scroll_speed
            y_top = y_base - height

            xw = self.note_xw.get(s["note"])
            if not xw:
                continue
            x, w, is_black = xw

            if y_top > self.screen_height or y_base < 0:
                continue

            base_color = _darken(BLUE, 25) if is_black else BLUE
            self._draw_bar_fx(x, y_top, w, height, base_color)

    def update_bars(self, visible_spans, current_time, pressed_notes):
        self.screen.fill(BLACK)
        self.draw_note_bars_upwards(visible_spans, current_time)
        self.draw_keyboard(pressed_notes)
        pygame.display.flip()
        self.clock.tick(FPS)
