import threading

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

# Converte .mid -> .ogg quando houver SoundFont local (não bloqueia o jogo)
convert_all_mid_to_ogg()

graphics = Graphics()

# Splash (2s)
if not show_splash(graphics):
    graphics.quit()
    raise SystemExit

app_running = True
while app_running:
    # Menu (retorna dict: {"action":"start","midi":"..."} ou {"action":"quit"})
    menu_result = run_menu(graphics)
    if menu_result.get("action") != "start":
        break

    chosen_midi = menu_result.get("midi", "fairy_tale.mid")

    # Recarrega config (pode ter mudado nos Ajustes)
    cfg = load_config()

    # Contagem "prepare-se"
    show_countdown(graphics)

    # Engine + música (se habilitada)
    engine = GameEngine(chosen_midi)
    engine.start()
    if cfg.get("music_enabled", True):
        # usa volume do config dentro do play_music()
        play_music(chosen_midi)

    # Porta MIDI
    pressed_notes = set()
    port = open_midi_port()

    # LiveSynth (som do teclado) — sem nota de teste: diagnose_and_test=False
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
            # Eco ao vivo (se habilitado)
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

            # Lógica do jogo
            if msg.type == "note_on" and msg.velocity > 0:
                pressed_notes.add(msg.note)
                engine.check_note_input(msg.note)
            elif msg.type == "note_off" or (
                msg.type == "note_on" and msg.velocity == 0
            ):
                pressed_notes.discard(msg.note)

    threading.Thread(target=midi_listener, daemon=True).start()

    # Loop do jogo — ESC volta pro menu, fechar janela encerra app
    back_to_menu = False
    quit_requested = False
    try:
        running = True
        while running and not engine.is_finished():
            # tratamos eventos aqui para distinguir ESC de fechar janela
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit_requested = True
                    running = False
                    break
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    back_to_menu = True
                    running = False
                    break

            if not running:
                break

            current_time = engine.get_current_time()
            visible_spans = engine.get_visible_spans(current_time)
            graphics.update_bars(visible_spans, current_time, pressed_notes)

    finally:
        # limpeza
        try:
            port.close()
        except Exception:
            pass
        if live:
            live.close()
        stop_music()

    if quit_requested:
        app_running = False
    elif back_to_menu:
        # volta ao while app_running para reabrir o menu
        continue
    else:
        # música terminou normalmente: volta ao menu também
        continue

graphics.quit()
