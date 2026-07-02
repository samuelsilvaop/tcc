from __future__ import annotations

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
from midi_game.midi_warning import show_no_midi_screen
from midi_game.save_data import register_score
from midi_game.sounds import play_music, preload_music, stop_music
from midi_game.splash import show_splash

PRE_ROLL_SECONDS = 2.0  # espera extra após 3-2-1
HIT_WINDOW = 0.08  # 80ms de tolerância para engatar a nota *antes* do início dela
MAX_SPAN_SCORE = (
    100  # pontos máximos por span quando segurou 100% do tempo (sem penalidade)
)


def try_hit(note: int, visible_spans: list[dict], current_time: float):
    """Encontra o span mais próximo (da mesma nota) que ainda pode ser engatado.

    O engate pode acontecer um pouco antes do início (tolerância HIT_WINDOW) ou
    a qualquer momento durante a duração da nota (engate tardio: os pontos são
    contados só a partir do aperto, proporcional ao tempo restante do span, com
    a pior faixa de qualidade de `_timing_multiplier`). Não é possível engatar
    depois que a nota já terminou.
    """
    best = None
    best_dt = float("inf")
    for s in visible_spans:
        if s["note"] != note:
            continue
        if current_time > s["end"] or current_time < s["start"] - HIT_WINDOW:
            continue
        dt = abs(s["start"] - current_time)
        if dt < best_dt:
            best_dt = dt
            best = s
    if best is not None:
        return best, best_dt
    return None, None


def _timing_multiplier(dt: float) -> float:
    """Penalidade por timing no momento do engate (note_on).

    `dt` é a distância (em segundos, sempre >= 0) entre o aperto e o início da
    nota. Engates tardios (fora da janela de 80ms) sempre caem na pior faixa.
    """
    if dt < 0.03:
        return 1.0
    if dt < 0.06:
        return 0.7
    return 0.4


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

            # carrega o audio ja aqui (durante o 3-2-1) pra que o play_music()
            # la na frente so precise dar .play(), sem I/O/decodificacao no
            # frame exato do gatilho -- isso e o que causava o atraso do
            # audio em relacao as notas na tela.
            if cfg.get("music_enabled", True):
                preload_music(chosen_midi)

            if not show_countdown(graphics):
                app_running = False
                break

            graphics.reset_score()

            # sincronismo (ajuste fino)
            sync_offset = float(cfg.get("sync_offset", 0.0))
            music_enabled = cfg.get("music_enabled", True)

            engine = GameEngine(chosen_midi)
            max_score = engine.get_max_score(max_per_span=MAX_SPAN_SCORE)

            # engine começa no futuro (pré-roll visual)
            t_start = time.time() + PRE_ROLL_SECONDS
            engine.start(start_time=t_start)

            # Porta MIDI
            pressed_notes: set[int] = set()
            just_pressed: list[int] = []  # notas apertadas desde o último frame
            # protege just_pressed: sem isso, um note_on da thread do MIDI
            # bem entre o "list(just_pressed)" e o "just_pressed.clear()" do
            # loop principal seria perdido silenciosamente (nunca engataria
            # o span daquela nota, mesmo com o timing certo).
            just_pressed_lock = threading.Lock()

            # Porta MIDI (obrigatória)
            port = None
            while port is None:
                port, ok = open_midi_port()

                if ok:
                    break

                # mostra aviso na tela (jogador)
                action = show_no_midi_screen(graphics)

                if action == "menu":
                    stop_music()
                    port = None
                    break

                if action == "quit":
                    graphics.quit()
                    raise SystemExit

                # retry -> volta no loop e tenta de novo

            # se voltou ao menu (sem teclado), reinicia o while do menu
            if port is None:
                continue

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
                        with just_pressed_lock:
                            just_pressed.append(msg.note)
                    elif msg.type == "note_off" or (
                        msg.type == "note_on" and msg.velocity == 0
                    ):
                        pressed_notes.discard(msg.note)

            threading.Thread(target=midi_listener, daemon=True).start()

            music_started = False

            # evita pontuar 2x o mesmo span
            finished_spans: set[tuple[int, float, float]] = set()

            # spans que passaram do fim sem nunca ter sido engatados (miss)
            missed_spans: set[tuple[int, float, float]] = set()

            # spans "engatados": nota correta pressionada -> acumula pontos proporcional ao tempo segurado
            active_hits: dict[int, dict] = {}  # note -> state

            try:
                running = True
                while running:
                    running = graphics.handle_events()

                    # tempo real do engine (pode ser negativo durante pré-roll)
                    t_engine = engine.get_current_time()

                    # Uma vez que a musica comecou, usamos o relogio de
                    # playback real do mixer (get_pos(), em ms desde o play())
                    # em vez do relogio de parede (time.time()) -- assim a
                    # sincronia reflete a latencia de audio de verdade do
                    # driver/SO em uso, em vez de so assumir que o som comecou
                    # exatamente no instante em que play() foi chamado.
                    pos_ms = (
                        pygame.mixer.music.get_pos()
                        if music_started and music_enabled
                        else -1
                    )
                    if pos_ms >= 0:
                        t_visual = (pos_ms / 1000.0) + sync_offset
                    else:
                        t_visual = t_engine + sync_offset

                    spans = engine.get_visible_spans(
                        t_visual, window_ahead=8.0, window_behind=1.0
                    )
                    graphics.update_bars(spans, t_visual, pressed_notes)

                    # inicia música exatamente quando "tempo 0" chega
                    if (not music_started) and t_engine >= 0:
                        if music_enabled:
                            play_music(chosen_midi)
                        music_started = True

                    # NOTE_ON -> tenta "engatar" um span
                    with just_pressed_lock:
                        pending = list(just_pressed)
                        just_pressed.clear()
                    if pending:
                        for note in pending:
                            s, dt = try_hit(note, spans, t_visual)
                            if not s:
                                continue

                            span_key = (s["note"], s["start"], s["end"])
                            if span_key in finished_spans:
                                continue

                            # se já tá engatado exatamente esse span nessa nota, ignora
                            if (
                                note in active_hits
                                and active_hits[note].get("span_key") == span_key
                            ):
                                continue

                            quality = _timing_multiplier(float(dt))
                            rate = engine.get_span_points_rate(
                                s, max_span_score=MAX_SPAN_SCORE
                            )

                            # começa a contar a partir do instante atual (clamp no início do span)
                            last_t = max(float(t_visual), float(s["start"]))

                            active_hits[note] = {
                                "span_key": span_key,
                                "start": float(s["start"]),
                                "end": float(s["end"]),
                                "rate": float(
                                    rate
                                ),  # pontos por segundo (p/ esse span)
                                "quality": float(
                                    quality
                                ),  # penalidade por timing no engate
                                "last_t": float(
                                    last_t
                                ),  # último tempo computado dentro do span
                                "earned": 0.0,  # pontos ganhos nesse span
                                "max_allowed": float(MAX_SPAN_SCORE) * float(quality),
                            }

                            # feedback visual do engate (sem pontuar aqui)
                            graphics.register_hit_start(note, span_key)

                    # acumula pontos por frame para spans engatados
                    now_t = float(t_visual)
                    to_remove: list[int] = []

                    for note, st in list(active_hits.items()):
                        span_key = st["span_key"]
                        end_t = st["end"]

                        # se soltou a tecla, finaliza
                        if note not in pressed_notes:
                            to_remove.append(note)
                            continue

                        # calcula delta de tempo dentro do span
                        t1 = min(now_t, end_t)
                        dt_hold = t1 - st["last_t"]
                        if dt_hold > 0:
                            add = st["rate"] * dt_hold * st["quality"]

                            # trava pra nunca passar do máximo do span (já considerando qualidade)
                            remaining = st["max_allowed"] - st["earned"]
                            if remaining <= 0:
                                add = 0.0
                            elif add > remaining:
                                add = remaining

                            if add > 0:
                                st["earned"] += add
                                st["last_t"] = t1
                                graphics.add_score(add)

                        # terminou o span pelo tempo -> finaliza
                        if now_t >= end_t:
                            to_remove.append(note)

                    # finalizações: popup 1x com o total ganho naquele span
                    for note in to_remove:
                        st = active_hits.pop(note, None)
                        if not st:
                            continue

                        span_key = st["span_key"]
                        finished_spans.add(span_key)

                        gained = int(round(st["earned"]))
                        if gained > 0:
                            graphics.popup_score(note, gained)
                            graphics.flash_bar(span_key)

                    # spans que passaram do fim sem nunca ter sido engatados
                    # (nem em active_hits, nem finalizados acima) -> miss total
                    for s in spans:
                        span_key = (s["note"], s["start"], s["end"])
                        if span_key in finished_spans or span_key in missed_spans:
                            continue
                        if now_t > s["end"]:
                            missed_spans.add(span_key)
                            graphics.popup_miss(s["note"])
                            graphics.flash_bar_miss(span_key)

                    # terminou? (engine ou audio)
                    # so' considera o audio pra decidir o fim se ele de fato
                    # foi tocado -- com music_enabled=False, music_started vira
                    # True sem nunca chamar play_music(), e get_busy() sempre
                    # retorna False (nada tocando), o que antes encerrava a
                    # musica no frame seguinte ao pre-roll, antes do jogador
                    # conseguir tocar qualquer nota.
                    audio_done = (
                        music_started
                        and music_enabled
                        and (not pygame.mixer.music.get_busy())
                    )
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
            score = int(round(graphics.total_score))
            best_score, is_new_record = register_score(
                chosen_midi, score, max_score
            )

            action = graphics.show_results_screen(
                song_name=chosen_midi,
                max_score=max_score,
                best_score=best_score,
                is_new_record=is_new_record,
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
