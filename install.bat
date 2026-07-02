@echo off
REM install.bat - MIDI Hero (Windows)

setlocal enabledelayedexpansion

echo === MIDI Hero - Instalador Windows ===
echo.

REM ---- Faixa de versoes de Python compativeis com as dependencias (requirements.txt) ----
REM Hoje a restricao vem do pygame, que ainda nao publica wheels prontos fora desta
REM faixa (versoes mais novas do Python obrigam o pip a compilar do zero, o que costuma
REM falhar por falta do SDL2/toolchain). Se uma dependencia futura exigir outra faixa,
REM so ajustar as duas linhas abaixo -- o resto do script se adapta sozinho.
set "PY_VERSOES_SUPORTADAS=3.13 3.12 3.11 3.10 3.9"
set "PY_RECOMENDADA=3.12"

set "PY_CMD="

REM 1) Tenta achar, via "py launcher", alguma versao suportada ja instalada
where py >nul 2>&1
if not errorlevel 1 (
    for %%V in (%PY_VERSOES_SUPORTADAS%) do (
        if not defined PY_CMD (
            py -%%V --version >nul 2>&1
            if not errorlevel 1 set "PY_CMD=py -%%V"
        )
    )
)

REM 2) Sem "py launcher" com versao compativel: tenta o "python" do PATH
if not defined PY_CMD (
    python --version >nul 2>&1
    if not errorlevel 1 (
        for /f "delims=" %%V in ('python -c "import sys;print(f'{sys.version_info[0]}.{sys.version_info[1]}')"') do set "PY_VER=%%V"
        echo %PY_VERSOES_SUPORTADAS% | findstr /C:"!PY_VER!" >nul
        if not errorlevel 1 set "PY_CMD=python"
    )
)

if defined PY_CMD (
    for /f "delims=" %%I in ('%PY_CMD% --version 2^>^&1') do echo [OK] %%I encontrado ^(compativel^).
    goto :criar_venv
)

REM ---- Nenhuma versao compativel encontrada: pergunta se pode instalar ----
echo [AVISO] Nao foi encontrada uma instalacao de Python compativel com este jogo.
echo         Versoes suportadas: %PY_VERSOES_SUPORTADAS%
echo         Versao(oes) encontrada(s) no sistema:
python --version 2>nul
py --version 2>nul
if not defined PY_CMD echo         (nenhuma)
echo.
choice /C SN /M "Deseja instalar automaticamente o Python %PY_RECOMENDADA% agora (via winget)"
if errorlevel 2 goto :sem_instalar
if errorlevel 1 goto :instalar_python

:instalar_python
where winget >nul 2>&1
if errorlevel 1 (
    echo [ERRO] winget nao esta disponivel neste sistema.
    echo        Baixe manualmente o Python %PY_RECOMENDADA% em:
    echo        https://www.python.org/downloads/
    echo        Marque "Add python.exe to PATH" e a opcao do "py launcher" durante a instalacao.
    pause
    exit /b 1
)

echo Instalando Python %PY_RECOMENDADA% via winget, aguarde...
winget install --id Python.Python.3.12 -e --silent --accept-source-agreements --accept-package-agreements
if errorlevel 1 (
    echo [ERRO] Falha ao instalar o Python via winget.
    echo        Baixe manualmente em: https://www.python.org/downloads/
    pause
    exit /b 1
)

py -%PY_RECOMENDADA% --version >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Python foi instalado, mas nao foi reconhecido nesta janela.
    echo         Feche este terminal, abra um novo e rode install.bat de novo.
    pause
    exit /b 1
)
set "PY_CMD=py -%PY_RECOMENDADA%"
echo [OK] Python %PY_RECOMENDADA% instalado com sucesso.
goto :criar_venv

:sem_instalar
echo.
echo Instalacao cancelada. Baixe manualmente uma versao compativel (%PY_VERSOES_SUPORTADAS%) em:
echo https://www.python.org/downloads/
pause
exit /b 1

:criar_venv
if not exist ".venv" (
    echo Criando ambiente virtual...
    %PY_CMD% -m venv .venv
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
