# Makefile - MIDI Hero
# Funciona em Linux e macOS. Para Windows use install.bat

# pygame 2.6.1 tem um bug de import circular em Python 3.14+ (ver
# https://github.com/pygame/pygame/issues/4795), entao evitamos o "python3"
# do sistema se ele for uma versao mais nova que essa faixa. Pode forcar uma
# versao especifica com: make PYTHON=python3.12 install
PY_VERSOES_SUPORTADAS := 3.13 3.12 3.11 3.10 3.9
PYTHON  ?= $(shell for v in $(PY_VERSOES_SUPORTADAS); do command -v python$$v >/dev/null 2>&1 && { echo python$$v; break; }; done)
ifeq ($(strip $(PYTHON)),)
PYTHON := python3
endif
VENV    := .venv
PIP     := $(VENV)/bin/pip
PYEXEC  := $(VENV)/bin/python

.PHONY: all install run clean uninstall help

all: install

# ------------------------------------------------------------------
# install: cria venv e instala dependências Python
# ------------------------------------------------------------------
install: $(VENV)/bin/activate
	@echo ""
	@echo "=== Dependencias Python instaladas ==="
	@echo ""
	@echo "IMPORTANTE: instale tambem as ferramentas do sistema:"
	@$(MAKE) --no-print-directory _sys_hint
	@echo ""
	@echo "E coloque um arquivo .sf2 (SoundFont) em:"
	@echo "  midi_game/assets/sf2/"
	@echo ""
	@echo "Para rodar o jogo:  make run"

$(VENV)/bin/activate: requirements.txt
	@ver=$$($(PYTHON) -c 'import sys; print("%d.%d" % sys.version_info[:2])'); \
	case " $(PY_VERSOES_SUPORTADAS) " in \
		*" $$ver "*) : ;; \
		*) echo "[AVISO] $(PYTHON) e Python $$ver, fora da faixa suportada ($(PY_VERSOES_SUPORTADAS))."; \
		   echo "        Instale uma dessas versoes e rode: make PYTHON=python3.12 install"; ;; \
	esac
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@touch $(VENV)/bin/activate

# ------------------------------------------------------------------
# run: executa o jogo dentro do venv
# ------------------------------------------------------------------
run: $(VENV)/bin/activate
	$(PYEXEC) main.py

# ------------------------------------------------------------------
# clean: remove cache e venv
# ------------------------------------------------------------------
clean:
	rm -rf $(VENV)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

# ------------------------------------------------------------------
# uninstall: desinstalador completo e interativo (venv, cache, dados
# salvos e, se confirmado, fluidsynth/ffmpeg do sistema)
# ------------------------------------------------------------------
uninstall:
	@bash uninstall.sh

# ------------------------------------------------------------------
# Dicas de instalação por sistema
# ------------------------------------------------------------------
_sys_hint:
	@UNAME=$$(uname -s 2>/dev/null || echo unknown); \
	if [ "$$UNAME" = "Linux" ]; then \
		if command -v pacman >/dev/null 2>&1; then \
			echo "  sudo pacman -S fluidsynth ffmpeg"; \
		elif command -v apt-get >/dev/null 2>&1; then \
			echo "  sudo apt-get install fluidsynth ffmpeg"; \
		elif command -v dnf >/dev/null 2>&1; then \
			echo "  sudo dnf install fluidsynth ffmpeg"; \
		else \
			echo "  Instale fluidsynth e ffmpeg pelo gerenciador do seu sistema."; \
		fi; \
	elif [ "$$UNAME" = "Darwin" ]; then \
		echo "  brew install fluid-synth ffmpeg"; \
	else \
		echo "  Instale fluidsynth e ffmpeg pelo gerenciador do seu sistema."; \
	fi

help:
	@echo "Comandos disponiveis:"
	@echo "  make install  - Cria venv e instala dependencias Python"
	@echo "  make run      - Executa o jogo"
	@echo "  make clean    - Remove venv e arquivos de cache"
	@echo "  make uninstall - Desinstalador completo e interativo (pede confirmacao)"
	@echo ""
	@echo "Para Windows: execute install.bat (instalar) ou uninstall.bat (desinstalar)"
