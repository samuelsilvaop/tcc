@echo off
REM install.bat - MIDI Hero (Windows)

setlocal enabledelayedexpansion

echo === MIDI Hero - Instalador Windows ===
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Baixe em: https://www.python.org/downloads/
    echo        Marque "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)

echo [OK] Python encontrado.

REM Cria ambiente virtual
if not exist ".venv" (
    echo Criando ambiente virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar ambiente virtual.
        pause
        exit /b 1
    )
)

echo Instalando dependencias Python...
.venv\Scripts\pip install --upgrade pip
.venv\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo === Dependencias Python instaladas com sucesso! ===
echo.
echo IMPORTANTE: Voce ainda precisa instalar manualmente:
echo.
echo   1) fluidsynth:
echo      winget install FluidSynth.FluidSynth
echo      ou: https://www.fluidsynth.org/download/
echo      Adicione o diretorio do fluidsynth ao PATH do sistema.
echo.
echo   2) ffmpeg:
echo      winget install Gyan.FFmpeg
echo      ou: https://ffmpeg.org/download.html
echo      Adicione o diretorio do ffmpeg ao PATH do sistema.
echo.
echo   3) SoundFont (.sf2):
echo      Coloque um arquivo .sf2 em: midi_game\assets\sf2\
echo      Sugestao: FluidR3_GM.sf2 (busque online por "FluidR3_GM.sf2 download")
echo.
echo Para rodar o jogo, execute: run.bat
echo.

REM Cria run.bat se nao existir
if not exist "run.bat" (
    echo @echo off > run.bat
    echo .venv\Scripts\python main.py >> run.bat
)

echo Instalacao concluida!
pause
