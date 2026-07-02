# midi_game/live_monitor.py
from __future__ import annotations

import glob
import os
import platform
import time
from pathlib import Path

import fluidsynth

SF2_FOLDER = Path(__file__).parent / "assets" / "sf2"

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
    last_err = None
    for drv in DRIVERS:
        try:
            # midi_driver='none': o jogo ja le o teclado MIDI via mido/rtmidi
            # (midi_input.py); sem isso o fluidsynth tenta abrir o mesmo
            # dispositivo MIDI e falha com "device already in use".
            fs.start(driver=drv, midi_driver="none")
            print(f"🎧 LiveSynth: driver de áudio em uso: {drv}")
            return drv
        except Exception as e:
            last_err = e
    if last_err:
        print(f"⚠️ LiveSynth: nenhum driver funcionou ({last_err})")
    return None


class LiveSynth:
    def __init__(self, sf2_path: str, sample_rate: int = 44100, gain: float = 1.5):
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
