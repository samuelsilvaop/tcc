import threading

from midi_game.audio_converter import convert_all_mid_to_ogg
from midi_game.game_engine import GameEngine
from midi_game.graphics import Graphics
from midi_game.menu import run_menu
from midi_game.midi_input import open_midi_port
from midi_game.sounds import play_music, stop_music
from midi_game.splash import show_splash

convert_all_mid_to_ogg()


engine = GameEngine("fairy_tale.mid")
graphics = Graphics()

# 1) Splash de 2s
if not show_splash(graphics):
    graphics.quit()
    raise SystemExit

# 2) Menu
if run_menu(graphics) != "start":
    graphics.quit()
    raise SystemExit
engine.start()
play_music("fairy_tale.mid")


pressed_notes = set()
port = open_midi_port()


def midi_listener():
    for msg in port:
        if msg.type == "note_on" and msg.velocity > 0:
            pressed_notes.add(msg.note)
            engine.check_note_input(msg.note)
        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            pressed_notes.discard(msg.note)


threading.Thread(target=midi_listener, daemon=True).start()

try:
    running = True
    while running and not engine.is_finished():
        running = graphics.handle_events()
        current_time = engine.get_current_time()
        active_events = engine.get_next_events()
        graphics.update(active_events, current_time, pressed_notes)
finally:
    try:
        port.close()
    except Exception:
        pass
    stop_music()
    graphics.quit()
