#!/usr/bin/env bash
# install.sh - MIDI Hero (Linux/macOS) - verifica e instala tudo que falta
#
# Cria o venv e instala as dependencias Python e, se o usuario autorizar a
# cada passo, tambem as dependencias de SISTEMA que faltarem: Homebrew
# (macOS), uma versao compativel de Python, fluidsynth e ffmpeg. Nada e
# instalado sem confirmacao explicita.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Faixa de versoes de Python compativeis (ver nota no README/Makefile: o
# pygame 2.6.1 tem um bug de import circular em Python 3.14+).
PY_VERSOES_SUPORTADAS=(3.13 3.12 3.11 3.10 3.9)
PY_RECOMENDADA="3.12"

VENV=".venv"
SF2_DIR="midi_game/assets/sf2"
SF2_URL="https://raw.githubusercontent.com/craffel/pretty-midi/main/pretty_midi/TimGM6mb.sf2"

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

baixar() {
    # baixar <url> <destino>
    if command -v curl >/dev/null 2>&1; then
        curl -fL -o "$2" "$1"
    elif command -v wget >/dev/null 2>&1; then
        wget -O "$2" "$1"
    else
        return 1
    fi
}

UNAME="$(uname -s 2>/dev/null || echo unknown)"

echo "=== MIDI Hero - Instalador (Linux/macOS) ==="
echo

# ----------------------------------------------------------------------
# 1) Gerenciador de pacotes do sistema
# ----------------------------------------------------------------------
PKG_INSTALL=""   # comando "sudo ... install -y" pronto pra receber pacotes
PKG_MANAGER=""

if [ "$UNAME" = "Darwin" ]; then
    PKG_MANAGER="brew"
    if ! command -v brew >/dev/null 2>&1; then
        echo "[AVISO] Homebrew nao encontrado (necessario para instalar Python,"
        echo "        fluidsynth e ffmpeg automaticamente no macOS)."
        if confirm "Instalar o Homebrew agora (script oficial brew.sh)?"; then
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            for p in /opt/homebrew/bin/brew /usr/local/bin/brew; do
                if [ -x "$p" ]; then eval "$("$p" shellenv)"; break; fi
            done
        fi
    fi
    if command -v brew >/dev/null 2>&1; then
        echo "[OK] Homebrew encontrado."
        PKG_INSTALL="brew install"
    else
        echo "[AVISO] Homebrew indisponivel; dependencias de sistema precisarao"
        echo "        ser instaladas manualmente."
    fi
elif [ "$UNAME" = "Linux" ]; then
    if command -v pacman >/dev/null 2>&1; then
        PKG_MANAGER="pacman"; PKG_INSTALL="sudo pacman -S --needed --noconfirm"
    elif command -v apt-get >/dev/null 2>&1; then
        PKG_MANAGER="apt"; PKG_INSTALL="sudo apt-get install -y"
    elif command -v dnf >/dev/null 2>&1; then
        PKG_MANAGER="dnf"; PKG_INSTALL="sudo dnf install -y"
    else
        echo "[AVISO] Gerenciador de pacotes nao reconhecido; dependencias de"
        echo "        sistema precisarao ser instaladas manualmente."
    fi
fi

# ----------------------------------------------------------------------
# 2) Python compativel (3.9-3.13)
# ----------------------------------------------------------------------
PY_BIN=""
for v in "${PY_VERSOES_SUPORTADAS[@]}"; do
    if command -v "python$v" >/dev/null 2>&1; then
        PY_BIN="python$v"
        break
    fi
done

if [ -n "$PY_BIN" ]; then
    echo "[OK] $($PY_BIN --version 2>&1) encontrado (compativel)."
else
    echo "[AVISO] Nenhuma versao de Python compativel encontrada (suportadas:"
    echo "        ${PY_VERSOES_SUPORTADAS[*]})."
    if [ -n "$PKG_INSTALL" ] && confirm "Instalar Python $PY_RECOMENDADA agora via $PKG_MANAGER?"; then
        case "$PKG_MANAGER" in
            brew)
                brew install "python@$PY_RECOMENDADA"
                PREFIX="$(brew --prefix "python@$PY_RECOMENDADA" 2>/dev/null)"
                [ -n "$PREFIX" ] && [ -x "$PREFIX/bin/python$PY_RECOMENDADA" ] && PY_BIN="$PREFIX/bin/python$PY_RECOMENDADA"
                ;;
            apt)
                $PKG_INSTALL "python$PY_RECOMENDADA" "python$PY_RECOMENDADA-venv" python3-pip \
                    || $PKG_INSTALL python3 python3-venv python3-pip
                ;;
            dnf)
                $PKG_INSTALL "python$PY_RECOMENDADA" python3-pip \
                    || $PKG_INSTALL python3 python3-pip
                ;;
            pacman)
                echo "[INFO] O Arch/Manjaro so mantem a versao mais recente do Python"
                echo "       nos repositorios oficiais, que pode ser mais nova que a"
                echo "       faixa suportada (${PY_VERSOES_SUPORTADAS[*]})."
                $PKG_INSTALL python python-pip
                ;;
        esac
        # Se nao resolvemos PY_BIN com um caminho especifico (caso do brew),
        # tenta achar de novo no PATH pelas versoes suportadas.
        if [ -z "$PY_BIN" ]; then
            for v in "${PY_VERSOES_SUPORTADAS[@]}"; do
                if command -v "python$v" >/dev/null 2>&1; then PY_BIN="python$v"; break; fi
            done
        fi
    fi
fi

if [ -z "$PY_BIN" ]; then
    # Ultimo recurso: usa o "python3" do sistema, mesmo fora da faixa suportada
    # (mesmo comportamento de fallback que o Makefile ja tinha).
    if command -v python3 >/dev/null 2>&1; then
        PY_BIN="python3"
        ver="$($PY_BIN -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
        echo "[AVISO] Usando python3 do sistema (versao $ver), fora da faixa"
        echo "        suportada (${PY_VERSOES_SUPORTADAS[*]}). O jogo pode nao"
        echo "        funcionar corretamente (ex.: bug do pygame em 3.14+)."
    else
        echo "[ERRO] Nenhum Python encontrado e nao foi possivel instalar um"
        echo "       automaticamente. Instale manualmente uma destas versoes:"
        echo "       ${PY_VERSOES_SUPORTADAS[*]}"
        exit 1
    fi
fi

# ----------------------------------------------------------------------
# 3) fluidsynth e ffmpeg
# ----------------------------------------------------------------------
instalar_dep_sistema() {
    local bin="$1" pkg="$2"
    if command -v "$bin" >/dev/null 2>&1; then
        echo "[OK] $bin encontrado."
        return
    fi
    echo "[AVISO] $bin nao encontrado."
    if [ -z "$PKG_INSTALL" ]; then
        echo "        Instale manualmente pelo gerenciador de pacotes do seu sistema."
        return
    fi
    if confirm "Instalar '$pkg' agora via: $PKG_INSTALL $pkg ?"; then
        $PKG_INSTALL "$pkg"
    else
        echo "[SKIP] $bin nao instalado; o jogo pode nao funcionar sem ele."
    fi
}

case "$PKG_MANAGER" in
    brew)   instalar_dep_sistema fluidsynth fluid-synth ;;
    *)      instalar_dep_sistema fluidsynth fluidsynth ;;
esac
instalar_dep_sistema ffmpeg ffmpeg

# ----------------------------------------------------------------------
# 4) Ambiente virtual + dependencias Python
# ----------------------------------------------------------------------
echo
if [ ! -d "$VENV" ]; then
    echo "Criando ambiente virtual com $PY_BIN..."
    "$PY_BIN" -m venv "$VENV"
fi

echo "Instalando dependencias Python..."
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/pip" install -r requirements.txt

# ----------------------------------------------------------------------
# 5) SoundFont (.sf2)
# ----------------------------------------------------------------------
echo
mkdir -p "$SF2_DIR"
if ls "$SF2_DIR"/*.sf2 >/dev/null 2>&1; then
    echo "[OK] SoundFont ja presente em $SF2_DIR."
else
    echo "[AVISO] Nenhum SoundFont (.sf2) encontrado em $SF2_DIR."
    echo "Baixando TimGM6mb.sf2 (~6MB, SoundFont GM leve)..."
    if baixar "$SF2_URL" "$SF2_DIR/TimGM6mb.sf2" && [ -s "$SF2_DIR/TimGM6mb.sf2" ]; then
        echo "[OK] SoundFont baixado com sucesso."
    else
        rm -f "$SF2_DIR/TimGM6mb.sf2"
        echo "[ERRO] Falha ao baixar o SoundFont automaticamente."
        echo "       Baixe manualmente e coloque em: $SF2_DIR"
        echo "       Sugestao: TimGM6mb.sf2 ou FluidR3_GM.sf2"
    fi
fi

echo
echo "=== Instalacao concluida! ==="
echo
echo "Para rodar o jogo:  make run"
