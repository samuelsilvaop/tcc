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

# inset visual p/ a barra não “encostar” na borda da tecla
WHITE_BAR_INSET_PX = 2
BLACK_BAR_INSET_PX = 2


def _is_black(note):
    return (note % 12) in (1, 3, 6, 8, 10)


class Graphics:
    def __init__(self):
        pygame.init()
        pygame.freetype.init()
        self.font = pygame.freetype.SysFont(None, 14)

        info = pygame.display.Info()
        self.screen = pygame.display.set_mode(
            (info.current_w, info.current_h), pygame.FULLSCREEN
        )
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        pygame.display.set_caption("MIDI Hero")

        self.clock = pygame.time.Clock()
        self.config = load_config()

        # Config
        self.num_keys = int(self.config["keyboard_keys"])
        self.lowest_note = int(self.config.get("lowest_note", 36))

        self.scroll_speed = 140  # px/s

        # --- construir layout das brancas
        white_notes = []
        for n in range(self.lowest_note, self.lowest_note + self.num_keys):
            if not _is_black(n):
                white_notes.append(n)

        nW = len(white_notes)
        edges = [round(i * self.screen_width / nW) for i in range(nW + 1)]
        self.white_key_x = edges[:-1]
        self.white_key_w = [edges[i + 1] - edges[i] for i in range(nW)]
        self.white_notes = white_notes  # manter lista, mesma ordem da tela

        # --- mapa de semitom -> (x, w, is_black)
        # percorre o range na ordem do teclado, acompanhando a “janela” entre brancas adjacentes
        self.note_xw = {}  # dict[int] -> (x, w, is_black)
        w_idx = 0  # índice da branca "corrente" (esquerda)

        for n in range(self.lowest_note, self.lowest_note + self.num_keys):
            if not _is_black(n):
                # branca ocupa a faixa [white_x[w_idx], white_x[w_idx]+white_w[w_idx]]
                x = self.white_key_x[w_idx] + WHITE_BAR_INSET_PX
                w = max(2, self.white_key_w[w_idx] - 2 * WHITE_BAR_INSET_PX)
                self.note_xw[n] = (x, w, False)
                w_idx += 1  # avança “janela” da esquerda
            else:
                # preta fica centrada na borda entre a branca à esquerda (w_idx-1) e a da direita (w_idx)
                left_i = max(0, w_idx - 1)
                right_i = min(len(self.white_key_x) - 1, w_idx)

                # borda entre brancas: canto direito da branca da esquerda
                border_x = self.white_key_x[left_i] + self.white_key_w[left_i]

                # largura ~ 60% da menor branca vizinha (fica bonito e proporcional)
                left_w = self.white_key_w[left_i]
                right_w = self.white_key_w[right_i]
                bw_raw = int(min(left_w, right_w) * 0.6)
                bw = max(6, bw_raw - 2 * BLACK_BAR_INSET_PX)

                x = border_x - (bw // 2) + BLACK_BAR_INSET_PX
                self.note_xw[n] = (x, bw, True)

        # compat antigo (não usamos mais no update)
        self.key_width = self.screen_width // self.num_keys

    def note_name(self, note_number):
        names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        name = names[note_number % 12]
        octave = note_number // 12 - 1
        return f"{name}{octave}"

    # ---------- TECLADO ----------
    def draw_keyboard(self, pressed_notes=None):
        if pressed_notes is None:
            pressed_notes = []

        # Brancas
        for i, note in enumerate(self.white_notes):
            x = self.white_key_x[i]
            w = self.white_key_w[i]
            color = GREEN if note in pressed_notes else WHITE
            pygame.draw.rect(
                self.screen,
                color,
                (x, self.screen_height - WHITE_KEY_HEIGHT, w, WHITE_KEY_HEIGHT),
            )
            pygame.draw.rect(
                self.screen,
                BLACK,
                (x, self.screen_height - WHITE_KEY_HEIGHT, w, WHITE_KEY_HEIGHT),
                1,
            )
            self.font.render_to(
                self.screen,
                (x + 4, self.screen_height - 20),
                self.note_name(note),
                BLACK,
            )

        # Pretas (usar o mesmo critério do mapa para posicionar)
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
                    (x, self.screen_height - WHITE_KEY_HEIGHT, bw, BLACK_KEY_HEIGHT),
                )
                self.font.render_to(
                    self.screen,
                    (x + 2, self.screen_height - WHITE_KEY_HEIGHT + 10),
                    self.note_name(black_note),
                    WHITE,
                )

    # ---------- modo antigo (não usado no update) ----------
    def draw_notes(self, active_notes, current_time):
        for e in active_notes:
            if e.get("type") != "note_on":
                continue
            xw = self.note_xw.get(e["note"])
            if not xw:
                continue
            x, w, _ = xw
            y = (
                self.screen_height
                - WHITE_KEY_HEIGHT
                - ((e["time"] - current_time) * 100)
            )
            if 0 <= x <= self.screen_width and 0 <= y <= self.screen_height:
                pygame.draw.rect(self.screen, BLUE, (x, y, w, NOTE_HEIGHT))

    def update(self, active_notes, current_time, pressed_notes):
        self.screen.fill(BLACK)
        # self.draw_notes(active_notes, current_time)  # desativado
        self.draw_keyboard(pressed_notes)
        pygame.display.flip()
        self.clock.tick(FPS)

    # ---------- EVENTOS ----------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
        return True

    def quit(self):
        pygame.quit()

    # ---------- BARRAS (Guitar-Hero) ----------
    def draw_note_bars_upwards(self, spans, current_time):
        hit_line_y = self.screen_height - WHITE_KEY_HEIGHT
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
            x, w, _ = xw

            if y_top > self.screen_height or y_base < 0:
                continue

            pygame.draw.rect(self.screen, BLUE, (x, y_top, w, height))

    def update_bars(self, visible_spans, current_time, pressed_notes):
        self.screen.fill(BLACK)
        self.draw_note_bars_upwards(visible_spans, current_time)
        self.draw_keyboard(pressed_notes)
        pygame.display.flip()
        self.clock.tick(FPS)
