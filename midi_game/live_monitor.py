# midi_game/live_monitor.py
import glob
import os
import time

import fluidsynth

SF2_FOLDER = "midi_game/assets/sf2"

SEARCH_PATHS = [
    # projeto
    os.path.join(SF2_FOLDER, "*.sf2"),
    # locais comuns no Linux
    "/usr/share/sounds/sf2/*.sf2",
    "/usr/share/soundfonts/*.sf2",
    os.path.expanduser("~/.soundfonts/*.sf2"),
    os.path.expanduser("~/.local/share/soundfonts/*.sf2"),
    # macOS (instalações comuns)
    "/Library/Audio/Sounds/Banks/*.sf2",
    os.path.expanduser("~/Library/Audio/Sounds/Banks/*.sf2"),
    # Windows (ex.: CoolSoft VirtualMIDISynth SoundFonts)
    os.path.expanduser("~/AppData/Local/VirtualMIDISynth/*.sf2"),
]

DRIVERS = ("pulseaudio", "alsa", "sdl2", "coreaudio", "dsound", "portaudio", "jack")


def _find_soundfont():
    os.makedirs(SF2_FOLDER, exist_ok=True)
    for pattern in SEARCH_PATHS:
        for path in glob.glob(pattern):
            if os.path.isfile(path):
                return path
    return None


def _try_start(fs):
    last_err = None
    for drv in DRIVERS:
        try:
            fs.start(driver=drv)
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
            "⚠️ LiveSynth: nenhum SoundFont (.sf2) encontrado. Coloque um em midi_game/assets/sf2/"
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
