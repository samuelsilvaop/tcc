import os
import tempfile

import ffmpeg
from mido import MidiFile  # vamos checar duração de forma simples

MIDI_FOLDER = "midi_game/assets/midi"
SF2_FOLDER = "midi_game/assets/sf2"
SAMPLE_RATE = 44100


def _pick_local_soundfont():
    """Retorna o caminho do primeiro .sf2 encontrado em assets/sf2, ou None."""
    os.makedirs(SF2_FOLDER, exist_ok=True)
    for fname in os.listdir(SF2_FOLDER):
        if fname.lower().endswith(".sf2"):
            return os.path.join(SF2_FOLDER, fname)
    return None


def _render_with_fluidsynth(sf2_path, midi_path, wav_path):
    """
    Renderiza MIDI → WAV usando o binário fluidsynth via ffmpeg-python (sem pydub).
    Observação: pyfluidsynth não expõe midi_file_play em todas as versões;
    para o TCC, a abordagem mais estável é invocar o fluidsynth CLI se disponível.
    """
    # Checagem simples de duração (para logs úteis)
    try:
        mid = MidiFile(midi_path)
        approx_sec = sum(m.time for m in mid) or 0.0
    except Exception:
        approx_sec = 0.0

    # Tenta usar o binário `fluidsynth` se existir
    fluidsynth_bin = _which("fluidsynth")
    if not fluidsynth_bin:
        raise RuntimeError(
            "fluidsynth não encontrado no sistema. "
            "Instale-o (ex.: pacman -S fluidsynth / apt install fluidsynth). "
            "Ou coloque um arquivo .ogg já pronto na pasta midi."
        )

    # Comando: fluidsynth -F out.wav -ni soundfont.sf2 musica.mid
    # Usamos ffmpeg-python só pra manter dependência de áudio consistente; aqui
    # chamaremos o fluidsynth via os.system/exec tradicional.
    import subprocess

    cmd = [
        fluidsynth_bin,
        "-ni",
        sf2_path,
        midi_path,
        "-F",
        wav_path,
        "-r",
        str(SAMPLE_RATE),
    ]
    subprocess.run(cmd, check=True)


def _which(cmd):
    """Retorna caminho absoluto do executável se existir no PATH, senão None."""
    from shutil import which

    return which(cmd)


def convert_all_mid_to_ogg():
    """
    Para cada .mid em assets/midi:
      - se já existe .ogg correspondente, pula;
      - se houver um .sf2 em assets/sf2, tenta renderizar .wav + converter pra .ogg;
      - se não houver .sf2, avisa e segue sem quebrar.
    """
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
            continue  # já convertido

        if not sf2:
            print(
                f"⚠️ Sem SoundFont (.sf2) em {SF2_FOLDER}. "
                f"Coloque um arquivo .sf2 (ex.: FluidR3_GM.sf2 ou GeneralUser GS.sf2) "
                f"para habilitar a música. Pulando conversão de {filename}."
            )
            continue

        print(
            f"🎼 Convertendo {filename} → {base}.ogg usando {os.path.basename(sf2)} ..."
        )

        # Renderiza para WAV temporário e converte para OGG
        with tempfile.TemporaryDirectory() as tmp:
            wav_path = os.path.join(tmp, f"{base}.wav")
            try:
                _render_with_fluidsynth(sf2, midi_path, wav_path)
                ffmpeg.input(wav_path).output(ogg_path, loglevel="quiet").run()
                print(f"✅ {base}.ogg gerado.")
            except Exception as e:
                print(f"❌ Erro ao converter {filename}: {e}")
