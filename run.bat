@echo off
REM run.bat - Executa MIDI Hero no Windows
if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] Ambiente virtual nao encontrado. Execute install.bat primeiro.
    pause
    exit /b 1
)
.venv\Scripts\python main.py
