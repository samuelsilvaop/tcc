import pygame
import pygame.freetype

from midi_game.config import load_config
from midi_game.fonts import get_font

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

        self.clock = pygame.time.Clock()
        self.config = load_config()
        self.flash_ms = int(self.config.get("hit_flash_ms", 100))

        # display
        self.screen = None
        self.screen_width = 0
        self.screen_height = 0

        self.num_keys = int(self.config["keyboard_keys"])
        self.lowest_note = int(self.config.get("lowest_note", 36))
        self.scroll_speed = 140

        # geometria
        self.WHITE_KEY_HEIGHT = 0
        self.BLACK_KEY_HEIGHT = 0
        self.white_notes = []
        self.white_key_x = []
        self.white_key_w = []
        self.note_xw = {}

        # fontes
        self.font_white = None
        self.font_black = None
        self.font_hud = None
        self.font_end_title = None
        self.font_end_hint = None

        # efeitos
        self.key_flash_until = {}
        self.bar_flash_until = {}
        self.score_popups = []
        self.font_popup = None

        # pontuacao
        self.total_score = 0.0

        self.refresh_display(force=True)

    def refresh_display(self, force: bool = False):
        info = pygame.display.Info()

        new_w = info.current_w
        new_h = info.current_h

        if (not force) and (new_w == self.screen_width and new_h == self.screen_height):
            return

        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("MIDI Hero")

        self.screen_width = new_w
        self.screen_height = new_h

        self.WHITE_KEY_HEIGHT = int(self.screen_height * 0.28)
        self.BLACK_KEY_HEIGHT = int(self.WHITE_KEY_HEIGHT * 0.66)

        white_font_size = max(12, int(self.WHITE_KEY_HEIGHT * 0.10))
        black_font_size = max(8, int(self.BLACK_KEY_HEIGHT * 0.09))

        self.font_white = get_font(white_font_size, bold=True)
        self.font_black = get_font(black_font_size, bold=True)

        # fontes HUD / telas (responsivo)
        hud_size = max(14, int(self.screen_height * 0.035))
        end_title_size = max(22, int(self.screen_height * 0.070))
        end_hint_size = max(14, int(self.screen_height * 0.040))
        self.font_hud = get_font(hud_size, bold=True)
        self.font_end_title = get_font(end_title_size, bold=True)
        self.font_end_hint = get_font(end_hint_size, bold=False)

        # layout das brancas
        white_notes = []
        for n in range(self.lowest_note, self.lowest_note + self.num_keys):
            if not _is_black(n):
                white_notes.append(n)

        nW = max(1, len(white_notes))
        edges = [round(i * self.screen_width / nW) for i in range(nW + 1)]
        self.white_key_x = edges[:-1]
        self.white_key_w = [edges[i + 1] - edges[i] for i in range(nW)]
        self.white_notes = white_notes

        # mapa nota -> (x,w,is_black)
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

    def reset_score(self):
        self.total_score = 0.0
        self.key_flash_until.clear()
        self.bar_flash_until.clear()
        self.score_popups.clear()

    def add_score(self, delta: float):
        """Soma pontos no placar sem criar popup/flash (usado para pontuação contínua)."""
        self.total_score += float(delta)

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
            now = pygame.time.get_ticks()
            flash = self.key_flash_until.get(note, 0) > now

            if flash:
                color = (255, 255, 120)
            else:
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

            text_x = x + max(4, int(w * 0.08))
            text_y = self.screen_height - max(10, int(self.WHITE_KEY_HEIGHT * 0.12))

            self.font_white.render_to(
                self.screen, (text_x, text_y), self.note_name(note), BLACK
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
                now = pygame.time.get_ticks()
                flash = self.key_flash_until.get(black_note, 0) > now

                if flash:
                    color = (255, 200, 80)
                else:
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

                text_x = x + max(2, int(bw * 0.06))
                text_y = (self.screen_height - self.WHITE_KEY_HEIGHT) + max(
                    4, int(self.BLACK_KEY_HEIGHT * 0.18)
                )

                self.font_black.render_to(
                    self.screen, (text_x, text_y), self.note_name(black_note), WHITE
                )

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_F5:
                    self.refresh_display(force=True)

        return True

    def quit(self):
        pygame.quit()

    def flash_bar(self, span_key):
        now = pygame.time.get_ticks()
        self.bar_flash_until[span_key] = now + self.flash_ms

    def register_hit_start(self, note: int, span_key):
        now = pygame.time.get_ticks()
        self.key_flash_until[note] = now + self.flash_ms
        self.bar_flash_until[span_key] = now + self.flash_ms

    def popup_score(self, note: int, score: int):
        now = pygame.time.get_ticks()
        xw = self.note_xw.get(note)
        if xw:
            x, w, _ = xw
            popup_x = x + w // 2
            popup_y = (
                self.screen_height
                - self.WHITE_KEY_HEIGHT
                - int(self.WHITE_KEY_HEIGHT * 0.25)
            )
            self.score_popups.append(
                {
                    "text": f"+{int(score)}",
                    "x": popup_x,
                    "y": popup_y,
                    "until": now + 600,
                }
            )

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

            span_key = (s["note"], s["start"], s["end"])
            now = pygame.time.get_ticks()
            flash = self.bar_flash_until.get(span_key, 0) > now

            if flash:
                base_color = (80, 255, 140)
            else:
                base_color = _darken(BLUE, 25) if is_black else BLUE

            self._draw_bar_fx(x, y_top, w, height, base_color)

    def _draw_hud(self):
        if not self.font_hud:
            return

        score_int = int(round(self.total_score))
        text = f"Pontos: {score_int}"
        rect = self.font_hud.get_rect(text)
        pad = max(6, int(self.screen_height * 0.008))
        box = pygame.Rect(pad, pad, rect.width + 2 * pad, rect.height + 2 * pad)
        pygame.draw.rect(self.screen, (0, 0, 0), box)
        pygame.draw.rect(self.screen, (80, 80, 80), box, 1)
        self.font_hud.render_to(
            self.screen, (box.x + pad, box.y + pad), text, (240, 240, 240)
        )

    def show_results_screen(self, song_name: str, max_score: int) -> str:
        score = int(round(self.total_score))
        max_score = max(1, int(max_score))
        pct = score / max_score

        if pct >= 0.95:
            msg = "ABSURDO. Mozart ficaria sem emprego."
        elif pct >= 0.80:
            msg = "Mandou bem! Quase profissional."
        elif pct >= 0.60:
            msg = "Dá pra ver que você tentou :)"
        elif pct >= 0.40:
            msg = "Ok... deu pra enganar."
        else:
            msg = "Parabéns! Uma nota pra você... dó!"

        title = "FIM DA MÚSICA"
        score_line = f"{score} / {max_score}  ({round(pct * 100)}%)"
        hint1 = "ENTER = voltar pro menu"
        hint2 = "R = jogar novamente | ESC = sair"

        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "quit"
                    if event.key == pygame.K_RETURN:
                        return "menu"
                    if event.key == pygame.K_r:
                        return "restart"

            self.screen.fill((0, 0, 0))

            y = int(self.screen_height * 0.18)
            x_center = self.screen_width // 2

            def draw_center(font, text, y, color=(240, 240, 240)):
                r = font.get_rect(text)
                font.render_to(self.screen, (x_center - r.width // 2, y), text, color)
                return y + r.height + int(self.screen_height * 0.02)

            y = draw_center(self.font_end_title, title, y)
            y = draw_center(self.font_end_hint, song_name, y, (180, 180, 180))
            y = draw_center(self.font_end_title, score_line, y, (200, 255, 255))
            y = draw_center(self.font_end_hint, msg, y)
            y += int(self.screen_height * 0.05)
            y = draw_center(self.font_end_hint, hint1, y, (180, 180, 180))
            _ = draw_center(self.font_end_hint, hint2, y, (180, 180, 180))

            pygame.display.flip()
            clock.tick(FPS)

    def update_bars(self, visible_spans, current_time, pressed_notes):
        self.screen.fill(BLACK)

        self.draw_note_bars_upwards(visible_spans, current_time)

        hit_line_y = self.screen_height - self.WHITE_KEY_HEIGHT
        y = hit_line_y - 3

        pygame.draw.line(
            self.screen, (60, 60, 60), (0, y - 1), (self.screen_width, y - 1), 1
        )
        pygame.draw.line(
            self.screen, (200, 255, 255), (0, y), (self.screen_width, y), 2
        )
        pygame.draw.line(
            self.screen, (60, 60, 60), (0, y + 2), (self.screen_width, y + 2), 1
        )

        self.draw_keyboard(pressed_notes)
        self.draw_popups()

        # HUD por cima
        self._draw_hud()

        pygame.display.flip()
        self.clock.tick(FPS)

    def draw_popups(self):
        if not self.font_popup:
            popup_size = max(12, int(self.WHITE_KEY_HEIGHT * 0.10))
            self.font_popup = get_font(popup_size, bold=True)

        now = pygame.time.get_ticks()
        alive = []
        for p in self.score_popups:
            if p["until"] <= now:
                continue

            t = (p["until"] - now) / 600.0
            y = int(p["y"] - (1 - t) * 25)

            rect = self.font_popup.get_rect(p["text"])
            self.font_popup.render_to(
                self.screen,
                (p["x"] - rect.width // 2, y),
                p["text"],
                (240, 240, 240),
            )
            alive.append(p)

        self.score_popups = alive
