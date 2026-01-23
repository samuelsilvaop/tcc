import os
import subprocess
import tempfile
from shutil import which

import ffmpeg

MIDI_FOLDER = "midi_game/assets/midi"
SF2_FOLDER = "midi_game/assets/sf2"
SAMPLE_RATE = 48000


def _pick_local_soundfont():
    """Retorna o caminho do primeiro .sf2 encontrado em assets/sf2, ou None."""
    os.makedirs(SF2_FOLDER, exist_ok=True)
    for fname in os.listdir(SF2_FOLDER):
        if fname.lower().endswith(".sf2"):
            return os.path.join(SF2_FOLDER, fname)
    return None


def _render_with_fluidsynth(sf2_path, midi_path, wav_path):
    """Renderiza MIDI → WAV usando o binário fluidsynth."""
    fluidsynth_bin = which("fluidsynth")
    if not fluidsynth_bin:
        raise RuntimeError(
            "fluidsynth não encontrado no sistema. "
            "Instale-o (ex.: pacman -S fluidsynth / apt install fluidsynth)."
        )

    cmd = [
        fluidsynth_bin,
        "-ni",  # Sem interface
        "-F",
        wav_path,  # Output file
        "-r",
        str(SAMPLE_RATE),  # Sample rate
        sf2_path,  # Soundfont
        midi_path,  # MIDI file
    ]

    subprocess.run(cmd, check=True, capture_output=True, text=True)


def convert_all_mid_to_ogg():
    """Converte todos os .mid em assets/midi para .ogg."""
    sf2 = _pick_local_soundfont()
    if not os.path.isdir(MIDI_FOLDER):
        os.makedirs(MIDI_FOLDER, exist_ok=True)

    for filename in os.listdir(MIDI_FOLDER):
        if not filename.lower().endswith(".mid"):
            continue

        base = os.path.splitext(filename)[0]
        midi_path = os.path.join(MIDI_FOLDER, filename)
        ogg_path = os.path.join(MIDI_FOLDER, f"{base}.ogg")

        if os.path.exists(ogg_path):
            continue

        if not sf2:
            print(
                f"⚠️ Sem SoundFont (.sf2) em {SF2_FOLDER}. "
                f"Pulando conversão de {filename}."
            )
            continue

        print(f"🎼 Convertendo {filename} → {base}.ogg...")

        with tempfile.TemporaryDirectory() as tmp:
            wav_path = os.path.join(tmp, f"{base}.wav")
            try:
                _render_with_fluidsynth(sf2, midi_path, wav_path)
                (
                    ffmpeg.input(wav_path)
                    .output(ogg_path, loglevel="quiet")
                    .overwrite_output()
                    .run()
                )
                print(f"✅ {base}.ogg gerado.")
            except subprocess.CalledProcessError as e:
                print(f"❌ Erro no fluidsynth: {e.stderr}")
            except Exception as e:
                print(f"❌ Erro ao converter {filename}: {e}")
