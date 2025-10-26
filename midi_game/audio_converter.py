import os

import ffmpeg
import requests
from midi2audio import FluidSynth as FSConverter  # alternativa real via wrapper

MIDI_FOLDER = "midi_game/assets/midi"
SOUNDFONT_PATH = "midi_game/assets/sf2/GeneralUserGS.sf2"
SOUNDFONT_URL = (
    "https://github.com/urish/cppfluid/raw/master/examples/FluidSynth/data/example.sf2"
)
SAMPLE_RATE = 44100


def ensure_soundfont():
    sf_dir = os.path.dirname(SOUNDFONT_PATH)
    os.makedirs(sf_dir, exist_ok=True)

    if os.path.exists(SOUNDFONT_PATH):
        return

    print("⬇️ Baixando SoundFont padrão...")

    try:
        r = requests.get(SOUNDFONT_URL, allow_redirects=True, timeout=10)
        if r.status_code == 200:
            with open(SOUNDFONT_PATH, "wb") as f:
                f.write(r.content)
            print("✅ SoundFont baixado com sucesso.")
        else:
            print(
                f"❌ Falha no download: {r.status_code}. O jogo continuará, mas sem som real."
            )
    except Exception as e:
        print(f"❌ Sem conexão: {e}. O jogo continuará, mas sem som real.")


def convert_all_mid_to_ogg():
    ensure_soundfont()

    for filename in os.listdir(MIDI_FOLDER):
        if filename.lower().endswith(".mid"):
            base = os.path.splitext(filename)[0]
            midi_path = os.path.join(MIDI_FOLDER, filename)
            wav_path = os.path.join(MIDI_FOLDER, f"{base}.wav")
            ogg_path = os.path.join(MIDI_FOLDER, f"{base}.ogg")

            if os.path.exists(ogg_path):
                continue

            print(f"🎼 Convertendo {filename} -> {base}.ogg")

            try:
                # Alternativa com midi2audio (mais confiável que usar Synth direto)
                converter = FSConverter(
                    sound_font=SOUNDFONT_PATH, sample_rate=SAMPLE_RATE
                )
                converter.midi_to_audio(midi_path, wav_path)

                ffmpeg.input(wav_path).output(ogg_path, loglevel="quiet").run()
                os.remove(wav_path)

                print(f"✅ {base}.ogg gerado com sucesso.")
            except Exception as e:
                print(f"❌ Erro ao converter {filename}: {e}")
