import threading

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

# Converte .mid -> .ogg quando houver SoundFont local (não bloqueia o jogo)
convert_all_mid_to_ogg()

graphics = Graphics()

# Splash (2s)
if not show_splash(graphics):
    graphics.quit()
    raise SystemExit

app_running = True
while app_running:
    # Menu
    menu_result = run_menu(graphics)
    if menu_result.get("action") != "start":
        break

    chosen_midi = menu_result.get("midi", "fairy_tale.mid")
    cfg = load_config()

    # “Prepare-se” 3-2-1
    show_countdown(graphics)

    # Engine + música (se habilitada)
    engine = GameEngine(chosen_midi)
    engine.start()
    if cfg.get("music_enabled", True):
        play_music(chosen_midi)

    # Porta MIDI
    pressed_notes = set()
    port = open_midi_port()

    # Som do teclado ao vivo
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
                engine.check_note_input(msg.note)
            elif msg.type == "note_off" or (
                msg.type == "note_on" and msg.velocity == 0
            ):
                pressed_notes.discard(msg.note)

    threading.Thread(target=midi_listener, daemon=True).start()

    try:
        running = True
        while running and not engine.is_finished():
            running = graphics.handle_events()  # ESC -> volta ao menu
            t = engine.get_current_time()
            spans = engine.get_visible_spans(t, window_ahead=8.0, window_behind=1.0)
            graphics.update_bars(spans, t, pressed_notes)
    finally:
        try:
            port.close()
        except Exception:
            pass
        if live:
            live.close()
        stop_music()

graphics.quit()
