@echo off
REM run.bat - Executa MIDI Hero no Windows
setlocal enabledelayedexpansion

if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] Ambiente virtual nao encontrado. Execute install.bat primeiro.
    pause
    exit /b 1
)

REM O install.bat baixa o fluidsynth (build oficial, sem instalador) dentro do
REM proprio projeto quando nao acha um no PATH. Se essa pasta local existir,
REM colocamos ela na frente do PATH so para este processo -- e o pacote Python
REM "fluidsynth" (pyfluidsynth) consegue achar a DLL via ctypes.
if exist "tools\fluidsynth\bin\fluidsynth.exe" (
    set "PATH=%~dp0tools\fluidsynth\bin;%PATH%"
)

.venv\Scripts\python main.py
