# Makefile - MIDI Hero
# Funciona em Linux e macOS. Para Windows use install.bat

VENV    := .venv
PIP     := $(VENV)/bin/pip
PYEXEC  := $(VENV)/bin/python

.PHONY: all install run clean uninstall help

all: install

# ------------------------------------------------------------------
# install: verifica/instala dependencias de sistema (Homebrew, Python,
# fluidsynth, ffmpeg - pedindo confirmacao a cada uma) e cria o venv
# com as dependencias Python. Ver install.sh.
# ------------------------------------------------------------------
install:
	@bash install.sh

$(VENV)/bin/activate: requirements.txt
	@bash install.sh

# ------------------------------------------------------------------
# run: executa o jogo dentro do venv (cria o venv primeiro se preciso)
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

help:
	@echo "Comandos disponiveis:"
	@echo "  make install  - Verifica/instala dependencias de sistema (Homebrew,"
	@echo "                  Python, fluidsynth, ffmpeg - pedindo confirmacao a"
	@echo "                  cada uma) e cria o venv com as dependencias Python"
	@echo "  make run      - Executa o jogo (cria o venv primeiro se preciso)"
	@echo "  make clean    - Remove venv e arquivos de cache"
	@echo "  make uninstall - Desinstalador completo e interativo (pede confirmacao)"
	@echo ""
	@echo "Para Windows: execute install.bat (instalar) ou uninstall.bat (desinstalar)"
