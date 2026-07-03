#!/usr/bin/env bash
# uninstall.sh - MIDI Hero (Linux/macOS) - Desinstalador completo
#
# Remove tudo que o "make install" / o jogo colocaram nesta pasta e, se voce
# pedir, tambem softwares do SISTEMA (fluidsynth, ffmpeg) que a Makefile
# sugere instalar via pacman/apt/dnf/brew. Como esses softwares podem estar
# sendo usados por OUTROS programas do seu computador (nao so por este
# jogo), cada remocao de sistema pede confirmacao a parte.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

confirm() {
    # confirm "pergunta" -> 0 (sim) se o usuario responder s/sim/y/yes
    local prompt="$1"
    local resp
    read -r -p "$prompt [s/N] " resp
    case "$resp" in
        [sS]|[sS][iI][mM]|[yY]|[yY][eE][sS]) return 0 ;;
        *) return 1 ;;
    esac
}

echo "=== MIDI Hero - Desinstalador (Linux/macOS) ==="
echo
echo "Este script remove os arquivos que o jogo/instalador criaram neste"
echo "projeto e, se voce pedir, tambem softwares do SISTEMA (fluidsynth,"
echo "ffmpeg) que podem estar em uso por OUTROS programas do seu computador,"
echo "nao so por este jogo. Por isso cada etapa pede confirmacao."
echo

if ! confirm "Continuar com a desinstalacao?"; then
    echo "Cancelado. Nada foi removido."
    exit 0
fi

echo
echo "--- 1) Arquivos locais do jogo (venv, cache Python) ---"
if confirm "Remover .venv/ e arquivos __pycache__/*.pyc deste projeto?"; then
    rm -rf .venv
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
    find . -name "*.pyc" -delete 2>/dev/null
    echo "[OK] Ambiente virtual e cache removidos."
else
    echo "[SKIP] Mantido."
fi

echo
echo "--- 2) SoundFont baixado (midi_game/assets/sf2/*.sf2) ---"
if ls midi_game/assets/sf2/*.sf2 >/dev/null 2>&1; then
    if confirm "Remover TODOS os arquivos .sf2 em midi_game/assets/sf2/ (inclui os que voce tenha colocado manualmente)?"; then
        rm -f midi_game/assets/sf2/*.sf2
        echo "[OK] SoundFonts removidos."
    else
        echo "[SKIP] Mantidos."
    fi
else
    echo "[OK] Nenhum SoundFont encontrado."
fi

echo
echo "--- 3) Progresso salvo e configuracoes (save_data.json, config.json) ---"
if confirm "Apagar recordes/progresso salvo e configuracoes do jogo?"; then
    rm -f midi_game/save_data.json midi_game/config.json
    echo "[OK] Dados de progresso/configuracao removidos."
else
    echo "[SKIP] Mantidos."
fi

echo
echo "=================================================================="
echo " ATENCAO: as proximas etapas desinstalam programas do SISTEMA, nao"
echo " so deste jogo. fluidsynth e ffmpeg podem estar sendo usados por"
echo " OUTROS softwares no seu computador. So continue se tiver certeza"
echo " de que nada mais no seu sistema depende deles."
echo "=================================================================="
echo

UNAME="$(uname -s 2>/dev/null || echo unknown)"

remove_pkg() {
    local pkg_name="$1"
    local cmd="$2"
    if confirm "Desinstalar '$pkg_name' do sistema via: $cmd ?"; then
        eval "$cmd"
    else
        echo "[SKIP] '$pkg_name' mantido."
    fi
}

if [ "$UNAME" = "Linux" ]; then
    if command -v pacman >/dev/null 2>&1; then
        command -v fluidsynth >/dev/null 2>&1 && remove_pkg fluidsynth "sudo pacman -Rns fluidsynth"
        command -v ffmpeg >/dev/null 2>&1 && remove_pkg ffmpeg "sudo pacman -Rns ffmpeg"
    elif command -v apt-get >/dev/null 2>&1; then
        command -v fluidsynth >/dev/null 2>&1 && remove_pkg fluidsynth "sudo apt-get remove fluidsynth"
        command -v ffmpeg >/dev/null 2>&1 && remove_pkg ffmpeg "sudo apt-get remove ffmpeg"
    elif command -v dnf >/dev/null 2>&1; then
        command -v fluidsynth >/dev/null 2>&1 && remove_pkg fluidsynth "sudo dnf remove fluidsynth"
        command -v ffmpeg >/dev/null 2>&1 && remove_pkg ffmpeg "sudo dnf remove ffmpeg"
    else
        echo "[INFO] Gerenciador de pacotes nao reconhecido; remova fluidsynth/ffmpeg"
        echo "       manualmente, se desejar."
    fi
elif [ "$UNAME" = "Darwin" ]; then
    if command -v brew >/dev/null 2>&1; then
        command -v fluidsynth >/dev/null 2>&1 && remove_pkg fluid-synth "brew uninstall fluid-synth"
        command -v ffmpeg >/dev/null 2>&1 && remove_pkg ffmpeg "brew uninstall ffmpeg"
    else
        echo "[INFO] Homebrew nao encontrado; remova fluidsynth/ffmpeg manualmente,"
        echo "       se desejar."
    fi
else
    echo "[INFO] SO nao reconhecido; fluidsynth/ffmpeg nao foram tocados."
fi

echo
echo "--- Python ---"
echo "[INFO] O Python do sistema (python3) NAO foi removido: este projeto"
echo "       nunca o instala, ele so usa o que ja existe no seu sistema."
echo "       Removê-lo poderia quebrar outros programas que dependem dele,"
echo "       entao isso precisa ser feito manualmente, pelo gerenciador de"
echo "       pacotes do seu SO, se voce realmente quiser."
echo

echo "=== Desinstalacao concluida ==="
