# midi_game/audio_converter.py
"""
Conversor híbrido MIDI -> OGG.

Regras (ordem):
1) Se já existe .ogg para um .mid, não faz nada.
2) Procura SoundFont (.sf2) em midi_game/assets/sf2 (repo).
3) Se não achar, tenta "soundfont_path" no config.json.
4) Se não achar, procura em caminhos comuns do sistema Linux.
5) Se ainda não achar:
   - tenta instalar automaticamente (somente em Linux, e somente se permitido),
     ou imprime instruções claras.
6) Renderiza MIDI->WAV com fluidsynth CLI e converte WAV->OGG com ffmpeg.

Observações importantes:
- Para instalar automaticamente, o usuário precisa ter permissões de sudo.
- Em ambientes sem sudo, o script só orienta.
"""

from __future__ import annotations

import os
import platform
import subprocess
import tempfile
from dataclasses import dataclass
from shutil import which
from typing import Iterable, Optional

import ffmpeg

from midi_game.config import load_config

MIDI_FOLDER = "midi_game/assets/midi"
SF2_FOLDER = "midi_game/assets/sf2"
SAMPLE_RATE = 48000


# -----------------------------
# Helpers: executáveis / sistema
# -----------------------------
def _is_linux() -> bool:
    return platform.system().lower() == "linux"


def _has_cmd(cmd: str) -> bool:
    return which(cmd) is not None


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    """
    Executa comando com stdout/stderr capturados (para logs e diagnóstico).
    """
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def _print_cmd_error(prefix: str, e: subprocess.CalledProcessError) -> None:
    msg = e.stderr.strip() if e.stderr else (e.stdout.strip() if e.stdout else str(e))
    print(f"❌ {prefix}: {msg}")


# -----------------------------
# SoundFont: localizar e instalar
# -----------------------------
def _pick_local_soundfont() -> Optional[str]:
    """Retorna o primeiro .sf2 encontrado na pasta do projeto, ou None."""
    os.makedirs(SF2_FOLDER, exist_ok=True)
    try:
        for fname in os.listdir(SF2_FOLDER):
            if fname.lower().endswith(".sf2"):
                return os.path.join(SF2_FOLDER, fname)
    except FileNotFoundError:
        return None
    return None


def _pick_config_soundfont() -> Optional[str]:
    """Tenta pegar soundfont_path do config.json (se existir e for válido)."""
    try:
        cfg = load_config()
    except Exception:
        return None

    sf2 = cfg.get("soundfont_path")
    if isinstance(sf2, str) and sf2.strip() and os.path.isfile(sf2):
        return sf2
    return None


def _common_system_soundfonts() -> Iterable[str]:
    """
    Lista de caminhos comuns em Linux.
    (Manjaro/Arch, Ubuntu/Debian etc.)
    """
    candidates = [
        "/usr/share/soundfonts/FluidR3_GM.sf2",
        "/usr/share/sounds/sf2/FluidR3_GM.sf2",
        "/usr/share/soundfonts/default.sf2",
        "/usr/share/sounds/sf2/default.sf2",
        "/usr/share/soundfonts/GeneralUser_GS.sf2",
        "/usr/share/sounds/sf2/GeneralUser_GS.sf2",
        "/usr/share/soundfonts/TimGM6mb.sf2",
        "/usr/share/sounds/sf2/TimGM6mb.sf2",
    ]
    # também tenta varrer diretórios comuns (se existirem)
    dirs = [
        "/usr/share/soundfonts",
        "/usr/share/sounds/sf2",
        "/usr/local/share/soundfonts",
        "/usr/local/share/sounds/sf2",
    ]
    for d in dirs:
        if os.path.isdir(d):
            try:
                for fname in os.listdir(d):
                    if fname.lower().endswith(".sf2"):
                        candidates.append(os.path.join(d, fname))
            except Exception:
                pass
    # remove duplicados preservando ordem
    seen = set()
    for p in candidates:
        if p not in seen:
            seen.add(p)
            yield p


def _pick_system_soundfont() -> Optional[str]:
    for p in _common_system_soundfonts():
        if os.path.isfile(p):
            return p
    return None


@dataclass
class InstallResult:
    ok: bool
    message: str


def _try_install_soundfont_linux() -> InstallResult:
    """
    Tenta instalar um pacote de SoundFont no Linux automaticamente.
    - Arch/Manjaro: fluid-soundfont-gm
    - Debian/Ubuntu: fluid-soundfont-gm
    Retorna ok/message.
    """
    if not _is_linux():
        return InstallResult(False, "Instalação automática só é suportada em Linux.")

    # precisa de sudo
    if not _has_cmd("sudo"):
        return InstallResult(
            False,
            "Não encontrei 'sudo' para instalar automaticamente. "
            "Instale manualmente um SoundFont (ex.: FluidR3_GM.sf2).",
        )

    # Detecta gerenciador
    if _has_cmd("pacman"):
        # Manjaro/Arch
        cmd = ["sudo", "pacman", "-S", "--noconfirm", "fluid-soundfont-gm"]
        try:
            print("📦 Tentando instalar SoundFont (pacman): fluid-soundfont-gm ...")
            _run(cmd, check=True)
            return InstallResult(True, "Instalado via pacman: fluid-soundfont-gm")
        except subprocess.CalledProcessError as e:
            _print_cmd_error("Falha ao instalar via pacman", e)
            return InstallResult(
                False,
                "Falha ao instalar via pacman. Tente manualmente: sudo pacman -S fluid-soundfont-gm",
            )

    if _has_cmd("apt-get"):
        # Debian/Ubuntu
        try:
            print("📦 Tentando instalar SoundFont (apt): fluid-soundfont-gm ...")
            _run(["sudo", "apt-get", "update"], check=True)
            _run(["sudo", "apt-get", "install", "-y", "fluid-soundfont-gm"], check=True)
            return InstallResult(True, "Instalado via apt: fluid-soundfont-gm")
        except subprocess.CalledProcessError as e:
            _print_cmd_error("Falha ao instalar via apt", e)
            return InstallResult(
                False,
                "Falha ao instalar via apt. Tente manualmente: sudo apt-get install fluid-soundfont-gm",
            )

    return InstallResult(
        False,
        "Não consegui detectar um gerenciador suportado (pacman/apt-get). "
        "Instale manualmente um SoundFont (ex.: FluidR3_GM.sf2).",
    )


def _resolve_soundfont(*, allow_auto_install: bool = True) -> Optional[str]:
    """
    Resolve soundfont seguindo a ordem:
    local -> config -> sistema -> (instalar) -> sistema novamente
    """
    sf2 = _pick_local_soundfont()
    if sf2:
        return sf2

    sf2 = _pick_config_soundfont()
    if sf2:
        return sf2

    sf2 = _pick_system_soundfont()
    if sf2:
        return sf2

    if allow_auto_install and _is_linux():
        res = _try_install_soundfont_linux()
        if res.ok:
            # depois de instalar, tenta achar de novo
            sf2 = _pick_system_soundfont()
            if sf2:
                return sf2
        else:
            print(f"⚠️ {res.message}")

    return None


# -----------------------------
# Conversão MIDI -> WAV -> OGG
# -----------------------------
def _render_with_fluidsynth(sf2_path: str, midi_path: str, wav_path: str) -> None:
    """
    Renderiza MIDI -> WAV usando fluidsynth CLI.

    OBS: O fluidsynth pode gerar logs; capturamos output para diagnosticar em erro.
    """
    fluidsynth_bin = which("fluidsynth")
    if not fluidsynth_bin:
        raise RuntimeError(
            "fluidsynth não encontrado no sistema. "
            "Instale-o (ex.: pacman -S fluidsynth / apt-get install fluidsynth)."
        )

    # fluidsynth -ni -F out.wav -r 48000 soundfont.sf2 file.mid
    cmd = [
        fluidsynth_bin,
        "-ni",
        "-F",
        wav_path,
        "-r",
        str(SAMPLE_RATE),
        sf2_path,
        midi_path,
    ]
    try:
        _run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        _print_cmd_error("Erro no fluidsynth", e)
        raise


def _ensure_tools_or_warn() -> bool:
    """
    Confere dependências externas. Retorna True se ok, False se deve abortar conversão.
    """
    ok = True
    if not _has_cmd("fluidsynth"):
        print("❌ fluidsynth não encontrado. Instale:")
        if _is_linux() and _has_cmd("pacman"):
            print("   sudo pacman -S fluidsynth")
        elif _is_linux() and _has_cmd("apt-get"):
            print("   sudo apt-get install fluidsynth")
        else:
            print("   (instale via gerenciador do seu sistema)")
        ok = False

    if not _has_cmd("ffmpeg"):
        print("❌ ffmpeg (binário) não encontrado. Instale:")
        if _is_linux() and _has_cmd("pacman"):
            print("   sudo pacman -S ffmpeg")
        elif _is_linux() and _has_cmd("apt-get"):
            print("   sudo apt-get install ffmpeg")
        else:
            print("   (instale via gerenciador do seu sistema)")
        ok = False

    return ok


def convert_all_mid_to_ogg(*, allow_auto_install_sf2: bool = True) -> None:
    """
    Para cada .mid em assets/midi:
      - se já existe .ogg correspondente, pula;
      - resolve .sf2 (local/config/sistema/instalação);
      - renderiza .wav temporário com fluidsynth;
      - converte para .ogg com ffmpeg.
    """
    if not os.path.isdir(MIDI_FOLDER):
        os.makedirs(MIDI_FOLDER, exist_ok=True)

    if not _ensure_tools_or_warn():
        return

    sf2 = _resolve_soundfont(allow_auto_install=allow_auto_install_sf2)
    if not sf2:
        print(
            f"⚠️ Nenhum SoundFont (.sf2) encontrado.\n"
            f"   - Coloque um .sf2 em: {SF2_FOLDER}\n"
            f"   - OU configure 'soundfont_path' no config.json\n"
            f"   - OU instale um soundfont do sistema (ex.: fluid-soundfont-gm)\n"
            f"   Conversão MIDI->OGG desabilitada por enquanto."
        )
        return

    # Converte todos os midis
    for filename in os.listdir(MIDI_FOLDER):
        if not filename.lower().endswith(".mid"):
            continue

        base = os.path.splitext(filename)[0]
        midi_path = os.path.join(MIDI_FOLDER, filename)
        ogg_path = os.path.join(MIDI_FOLDER, f"{base}.ogg")

        if os.path.exists(ogg_path):
            continue

        print(f"🎼 Convertendo {filename} → {base}.ogg (sf2: {os.path.basename(sf2)})")

        with tempfile.TemporaryDirectory() as tmp:
            wav_path = os.path.join(tmp, f"{base}.wav")
            try:
                _render_with_fluidsynth(sf2, midi_path, wav_path)

                # ffmpeg wav -> ogg
                (
                    ffmpeg.input(wav_path)
                    .output(ogg_path, loglevel="quiet")
                    .overwrite_output()
                    .run()
                )
                print(f"✅ {base}.ogg gerado.")
            except Exception as e:
                print(f"❌ Erro ao converter {filename}: {e}")
