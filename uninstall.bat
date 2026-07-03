@echo off
REM uninstall.bat - MIDI Hero (Windows) - Desinstalador completo
REM
REM Remove tudo que o install.bat / o jogo colocaram nesta pasta e, se voce
REM pedir, tambem softwares do SISTEMA (Python, ffmpeg, Visual C++
REM Redistributable) que o install.bat pode ter instalado via winget. Como
REM esses softwares podem estar sendo usados por OUTROS programas do seu PC
REM (nao so por este jogo), cada remocao de sistema pede confirmacao a parte.

setlocal enabledelayedexpansion

echo === MIDI Hero - Desinstalador Windows ===
echo.
echo Este script remove os arquivos que o instalador/jogo criaram nesta pasta
echo e, se voce pedir, tambem softwares do SISTEMA (Python, ffmpeg, Visual C++
echo Redistributable) que o install.bat pode ter instalado via winget. Esses
echo softwares podem estar sendo usados por OUTROS programas no seu PC, entao
echo cada um deles pede confirmacao separada antes de ser removido.
echo.

choice /C SN /M "Continuar com a desinstalacao"
if errorlevel 2 goto :cancelado

echo.
echo --- 1^) Arquivos locais do jogo (venv, cache Python, fluidsynth baixado) ---
choice /C SN /M "Remover .venv, __pycache__ e tools\fluidsynth deste projeto"
if errorlevel 2 goto :pula_local
if exist ".venv" rmdir /s /q ".venv"
if exist "tools\fluidsynth" rmdir /s /q "tools\fluidsynth"
for /d /r %%D in (__pycache__) do if exist "%%D" rmdir /s /q "%%D"
del /s /q *.pyc >nul 2>&1
echo [OK] Ambiente virtual, cache e fluidsynth local removidos.
goto :sf2

:pula_local
echo [SKIP] Mantido.

:sf2
echo.
echo --- 2^) SoundFont baixado (midi_game\assets\sf2\*.sf2) ---
dir /b "midi_game\assets\sf2\*.sf2" >nul 2>&1
if errorlevel 1 (
    echo [OK] Nenhum SoundFont encontrado.
    goto :dados
)
choice /C SN /M "Remover TODOS os .sf2 em midi_game\assets\sf2 (inclui os que voce tenha colocado manualmente)"
if errorlevel 2 goto :dados
del /q "midi_game\assets\sf2\*.sf2" >nul 2>&1
echo [OK] SoundFonts removidos.

:dados
echo.
echo --- 3^) Progresso salvo e configuracoes (save_data.json, config.json) ---
choice /C SN /M "Apagar recordes/progresso salvo e configuracoes do jogo"
if errorlevel 2 goto :sistema
if exist "midi_game\save_data.json" del /q "midi_game\save_data.json"
if exist "midi_game\config.json" del /q "midi_game\config.json"
echo [OK] Dados de progresso/configuracao removidos.

:sistema
echo.
echo ==================================================================
echo  ATENCAO: as proximas etapas desinstalam programas do SISTEMA, nao
echo  so deste jogo. Python, ffmpeg e o Visual C++ Redistributable
echo  costumam ser usados por OUTROS programas no seu PC. So continue
echo  se tiver certeza de que nada mais no seu computador depende deles.
echo ==================================================================
echo.

where winget >nul 2>&1
if errorlevel 1 (
    echo [INFO] winget nao esta disponivel neste sistema. Para remover
    echo        Python/ffmpeg/VC++ Redistributable manualmente, use
    echo        "Aplicativos instalados" nas Configuracoes do Windows.
    goto :fim
)

py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    choice /C SN /M "Desinstalar Python 3.12 (pode ter sido instalado via winget pelo install.bat)"
    if not errorlevel 2 (
        winget uninstall --id Python.Python.3.12 -e
    ) else (
        echo [SKIP] Python mantido.
    )
) else (
    echo [OK] Python 3.12 nao encontrado ^(nada a remover^).
)

where ffmpeg >nul 2>&1
if not errorlevel 1 (
    choice /C SN /M "Desinstalar ffmpeg (pode ter sido instalado via winget pelo install.bat)"
    if not errorlevel 2 (
        winget uninstall --id Gyan.FFmpeg -e
    ) else (
        echo [SKIP] ffmpeg mantido.
    )
) else (
    echo [OK] ffmpeg nao encontrado ^(nada a remover^).
)

echo.
echo [AVISO] O Visual C++ Redistributable e usado por uma quantidade enorme
echo         de programas Windows (jogos, drivers, outros softwares). NAO e
echo         recomendado remove-lo so por causa deste jogo. Prossiga apenas
echo         se tiver certeza do que esta fazendo.
choice /C SN /M "Desinstalar Visual C++ Redistributable mesmo assim"
if not errorlevel 2 (
    winget uninstall --id Microsoft.VCRedist.2015+.x64 -e
) else (
    echo [SKIP] Visual C++ Redistributable mantido.
)

:fim
echo.
echo === Desinstalacao concluida ===
pause
goto :eof

:cancelado
echo.
echo Desinstalacao cancelada. Nada foi removido.
pause
goto :eof
