import threading
import time

import pygame
from midi_game.audio_converter import convert_all_mid_to_ogg
from midi_game.config import load_config
from midi_game.countdown import show_countdown
from midi_game.game_engine import GameEngine
from midi_game.graphics import Graphics
from midi_game.live_monitor import create_live_synth
from midi_game.menu import run_menu
from midi_game.midi_input import open_midi_port
from midi_game.sounds import play_music, stop_music
from midi_game.splash import show_splash

PRE_ROLL_SECONDS = 2.0  # espera extra após 3-2-1
HIT_WINDOW = 0.08  # 80ms de tolerância


def try_hit(note: int, visible_spans: list[dict], current_time: float):
    """Encontra o span mais próximo (da mesma nota) e verifica se está dentro do HIT_WINDOW."""
    best = None
    best_dt = float("inf")
    for s in visible_spans:
        if s["note"] != note:
            continue
        dt = abs(s["start"] - current_time)
        if dt < best_dt:
            best_dt = dt
            best = s
    if best and best_dt <= HIT_WINDOW:
        return best, best_dt
    return None, None


def main():
    convert_all_mid_to_ogg()
    graphics = Graphics()

    if not show_splash(graphics):
        graphics.quit()
        raise SystemExit

    app_running = True
    while app_running:
        menu_result = run_menu(graphics)
        action = menu_result.get("action")
        if action != "start":
            break

        chosen_midi = menu_result.get("midi", "fairy_tale.mid")

        # loop da música atual (permite RESTART sem voltar pro menu)
        while True:
            cfg = load_config()
            graphics.refresh_display(force=True)

            if not show_countdown(graphics):
                app_running = False
                break

            graphics.reset_score()

            # sincronismo (ajuste fino)
            sync_offset = float(cfg.get("sync_offset", 0.0))

            engine = GameEngine(chosen_midi)
            max_score = engine.get_max_score(max_per_note=100)

            # engine começa no futuro (pré-roll visual)
            t_start = time.time() + PRE_ROLL_SECONDS
            engine.start(start_time=t_start)

            # Porta MIDI
            pressed_notes: set[int] = set()
            just_pressed: list[int] = []  # notas apertadas desde o último frame
            port = open_midi_port()

            # LiveSynth (som do teclado ao vivo)
            live = (
                create_live_synth(
                    diagnose_and_test=False, gain=float(cfg.get("live_volume", 0.5))
                )
                if cfg.get("live_keyboard_sound", False)
                else None
            )

            def midi_listener():
                sustain_down = False
                for msg in port:
                    # som ao vivo
                    if live and msg.type == "control_change" and msg.control == 64:
                        sustain_down = msg.value >= 64
                        live.sustain(sustain_down)
                    elif live and msg.type == "note_on" and msg.velocity > 0:
                        live.note_on(msg.note, msg.velocity)
                    elif live and (
                        msg.type == "note_off"
                        or (msg.type == "note_on" and msg.velocity == 0)
                    ):
                        live.note_off(msg.note)

                    # input do jogo
                    if msg.type == "note_on" and msg.velocity > 0:
                        pressed_notes.add(msg.note)
                        just_pressed.append(msg.note)
                    elif msg.type == "note_off" or (
                        msg.type == "note_on" and msg.velocity == 0
                    ):
                        pressed_notes.discard(msg.note)

            threading.Thread(target=midi_listener, daemon=True).start()

            music_started = False
            scored_spans: set[tuple[int, float, float]] = set()  # evita pontuar 2x

            try:
                running = True
                while running:
                    running = graphics.handle_events()

                    # tempo real do engine (pode ser negativo durante pré-roll)
                    t_engine = engine.get_current_time()

                    # tempo visual com offset (para acertar sincronia)
                    t_visual = t_engine + sync_offset

                    spans = engine.get_visible_spans(
                        t_visual, window_ahead=8.0, window_behind=1.0
                    )
                    graphics.update_bars(spans, t_visual, pressed_notes)

                    # inicia música exatamente quando "tempo 0" chega
                    if (not music_started) and t_engine >= 0:
                        if cfg.get("music_enabled", True):
                            play_music(chosen_midi)
                        music_started = True

                    # HIT: pontua somente quando a nota foi apertada (note_on)
                    if just_pressed:
                        pending = list(just_pressed)
                        just_pressed.clear()
                        for note in pending:
                            s, dt = try_hit(note, spans, t_visual)
                            if not s:
                                continue

                            span_key = (s["note"], s["start"], s["end"])
                            if span_key in scored_spans:
                                continue
                            scored_spans.add(span_key)

                            score = 100 if dt < 0.03 else 70 if dt < 0.06 else 40
                            graphics.register_hit(note, span_key, score)

                    # terminou? (engine ou audio)
                    audio_done = music_started and (not pygame.mixer.music.get_busy())
                    if engine.is_finished() or audio_done:
                        break

            finally:
                try:
                    port.close()
                except Exception:
                    pass
                if live:
                    live.close()
                stop_music()

            # terminou: mostra resultados
            action = graphics.show_results_screen(
                song_name=chosen_midi, max_score=max_score
            )

            if action == "restart":
                continue
            if action == "menu":
                break
            if action == "quit":
                app_running = False
                break

    graphics.quit()


if __name__ == "__main__":
    main()
