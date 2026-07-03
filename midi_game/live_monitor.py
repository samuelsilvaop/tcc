# midi_game/live_monitor.py
from __future__ import annotations

import contextlib
import glob
import os
import platform
import time
from pathlib import Path

# O pyfluidsynth carrega a lib nativa (libfluidsynth) no proprio import e
# levanta ImportError se ela nao estiver instalada no sistema. Como o main.py
# importa este modulo incondicionalmente, sem essa guarda o jogo crashava na
# inicializacao mesmo com o som ao vivo desligado (e mesmo com os .ogg ja
# prontos, situacao em que o FluidSynth nem e' necessario).
try:
    import fluidsynth
except Exception:
    fluidsynth = None

SF2_FOLDER = Path(__file__).parent / "assets" / "sf2"


@contextlib.contextmanager
def _suppress_native_stderr():
    """O fluidsynth e as libs de audio que ele tenta (ALSA, JACK, ...) escrevem
    direto no stderr do processo (fd 2) a nivel de C, entao redirect_stderr do
    Python nao pega -- so segura duplicando o file descriptor de verdade."""
    try:
        stderr_fd = 2
        saved_fd = os.dup(stderr_fd)
    except OSError:
        yield  # sem fd de stderr de verdade (ex.: alguns ambientes de teste)
        return
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull_fd, stderr_fd)
        yield
    finally:
        os.dup2(saved_fd, stderr_fd)
        os.close(devnull_fd)
        os.close(saved_fd)


_LOCAL_APP = os.environ.get("LOCALAPPDATA", "")

SEARCH_PATHS = [
    # projeto
    str(SF2_FOLDER / "*.sf2"),
    # locais comuns no Linux
    "/usr/share/sounds/sf2/*.sf2",
    "/usr/share/soundfonts/*.sf2",
    os.path.expanduser("~/.soundfonts/*.sf2"),
    os.path.expanduser("~/.local/share/soundfonts/*.sf2"),
    # macOS
    "/usr/local/share/soundfonts/*.sf2",
    "/opt/homebrew/share/soundfonts/*.sf2",
    "/Library/Audio/Sounds/Banks/*.sf2",
    os.path.expanduser("~/Library/Audio/Sounds/Banks/*.sf2"),
    # Windows
    os.path.join(_LOCAL_APP, "VirtualMIDISynth", "SoundFonts", "*.sf2"),
    r"C:\soundfonts\*.sf2",
]

_SYS = platform.system()
if _SYS == "Windows":
    DRIVERS = ("dsound", "portaudio", "sdl2")
elif _SYS == "Darwin":
    DRIVERS = ("coreaudio", "portaudio", "sdl2")
else:
    DRIVERS = ("pulseaudio", "pipewire", "alsa", "jack", "portaudio", "sdl2")


def _find_soundfont():
    SF2_FOLDER.mkdir(parents=True, exist_ok=True)
    for pattern in SEARCH_PATHS:
        for path in glob.glob(pattern):
            if os.path.isfile(path):
                return path
    return None


def _try_start(fs):
    # Nao usamos fs.start(): ele sempre cria tambem um driver de entrada MIDI
    # (new_fluid_midi_driver), e o jogo ja le o teclado MIDI via mido/rtmidi
    # (midi_input.py) -- isso gerava conflito ("device already in use") ou,
    # se a gente pedisse midi_driver="none", um erro porque essa build do
    # fluidsynth nem reconhece "none" como driver valido. Criando so o driver
    # de audio diretamente, o fluidsynth nunca tenta tocar no dispositivo MIDI.
    last_err = None
    for drv in DRIVERS:
        try:
            fs.setting("audio.driver", drv)
            audio_driver = fluidsynth.new_fluid_audio_driver(fs.settings, fs.synth)
            if audio_driver:
                fs.audio_driver = audio_driver
                print(f"🎧 LiveSynth: driver de áudio em uso: {drv}")
                return drv
            last_err = RuntimeError(f"driver '{drv}' nao inicializou")
        except Exception as e:
            last_err = e
    if last_err:
        print(f"⚠️ LiveSynth: nenhum driver funcionou ({last_err})")
    return None


class LiveSynth:
    def __init__(self, sf2_path: str, sample_rate: int = 44100, gain: float = 1.5):
        # A thread de audio que o fluidsynth sobe tenta ajustar a propria
        # prioridade de forma assincrona (e loga um aviso se falhar) alguns
        # instantes DEPOIS que new_fluid_audio_driver retorna -- por isso a
        # supressao cobre o __init__ inteiro (sfload/program_select ja dao
        # tempo de sobra pra esse aviso acontecer ainda dentro da janela).
        with _suppress_native_stderr():
            self.fs = fluidsynth.Synth(samplerate=sample_rate, gain=gain)
            drv = _try_start(self.fs)
            if not drv:
                raise RuntimeError(
                    "Nenhum driver de áudio disponível (pulseaudio/alsa/sdl2/etc)."
                )
            self.sfid = self.fs.sfload(sf2_path)
            if self.sfid < 0:
                raise RuntimeError(f"Falha ao carregar SoundFont: {sf2_path}")
            self.fs.program_select(0, self.sfid, 0, 0)
        print(f"🎹 LiveSynth: SoundFont em uso: {sf2_path}")

    def note_on(self, note: int, velocity: int = 100, ch: int = 0):
        self.fs.noteon(ch, max(0, min(note, 127)), max(0, min(velocity, 127)))

    def note_off(self, note: int, ch: int = 0):
        self.fs.noteoff(ch, max(0, min(note, 127)))

    def sustain(self, pressed: bool, ch: int = 0):
        self.fs.cc(ch, 64, 127 if pressed else 0)

    def stop_all(self):
        try:
            self.fs.system_reset()
        except Exception:
            pass

    def close(self):
        try:
            self.stop_all()
        finally:
            self.fs.delete()


def create_live_synth(diagnose_and_test: bool = True, gain: float = 0.5):
    if fluidsynth is None:
        print(
            "[AVISO] LiveSynth: biblioteca FluidSynth nao encontrada no sistema; "
            "som do teclado ao vivo desabilitado."
        )
        return None
    sf2 = _find_soundfont()
    if not sf2:
        print(
            f"[AVISO] LiveSynth: nenhum SoundFont (.sf2) encontrado. Coloque um em: {SF2_FOLDER}"
        )
        return None
    try:
        synth = LiveSynth(sf2_path=sf2, gain=gain)
        if diagnose_and_test:
            c4 = 60
            synth.note_on(c4, 100)
            time.sleep(0.25)
            synth.note_off(c4)
            print("✅ LiveSynth: teste rápido OK (C4 tocado).")
        return synth
    except Exception as e:
        print(f"⚠️ LiveSynth: não inicializado ({e})")
        return None
