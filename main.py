import threading
import time

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

PRE_ROLL_SECONDS = 2.0  # ✅ espera extra após 3-2-1

convert_all_mid_to_ogg()
graphics = Graphics()

if not show_splash(graphics):
    graphics.quit()
    raise SystemExit

app_running = True
while app_running:
    menu_result = run_menu(graphics)
    if menu_result.get("action") != "start":
        break

    chosen_midi = menu_result.get("midi", "fairy_tale.mid")
    cfg = load_config()

    # pega monitor/resolução atual
    graphics.refresh_display(force=True)

    if not show_countdown(graphics):
        break

    # ✅ sincronismo (ajuste fino):
    # +0.10 => barras "andam" 100ms adiantadas (compensa atraso do áudio)
    sync_offset = float(cfg.get("sync_offset", 0.0))

    engine = GameEngine(chosen_midi)

    # ✅ engine começa no futuro (pré-roll visual)
    t_start = time.time() + PRE_ROLL_SECONDS
    engine.start(start_time=t_start)

    # Porta MIDI
    pressed_notes = set()
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
            if live:
                if msg.type == "control_change" and msg.control == 64:
                    sustain_down = msg.value >= 64
                    live.sustain(sustain_down)
                elif msg.type == "note_on" and msg.velocity > 0:
                    live.note_on(msg.note, msg.velocity)
                elif msg.type in ("note_off",) or (
                    msg.type == "note_on" and msg.velocity == 0
                ):
                    live.note_off(msg.note)

            if msg.type == "note_on" and msg.velocity > 0:
                pressed_notes.add(msg.note)
                # só vale pontuar depois que a música começou (tempo >= 0)
                if engine.get_current_time() >= 0:
                    engine.check_note_input(msg.note)
            elif msg.type == "note_off" or (
                msg.type == "note_on" and msg.velocity == 0
            ):
                pressed_notes.discard(msg.note)

    threading.Thread(target=midi_listener, daemon=True).start()

    music_started = False

    try:
        running = True
        while running and not engine.is_finished():
            running = graphics.handle_events()

            # tempo real do engine (pode ser negativo durante pré-roll)
            t_engine = engine.get_current_time()

            # ✅ tempo visual com offset (para acertar sincronia)
            t_visual = t_engine + sync_offset

            spans = engine.get_visible_spans(
                t_visual, window_ahead=8.0, window_behind=1.0
            )
            graphics.update_bars(spans, t_visual, pressed_notes)

            # ✅ inicia música exatamente quando "tempo 0" chega
            if (not music_started) and t_engine >= 0:
                if cfg.get("music_enabled", True):
                    play_music(chosen_midi)
                music_started = True

    finally:
        try:
            port.close()
        except Exception:
            pass
        if live:
            live.close()
        stop_music()

graphics.quit()
