@echo off
REM install.bat - MIDI Hero (Windows)

setlocal enabledelayedexpansion

echo === MIDI Hero - Instalador Windows ===
echo.

REM ---- Faixa de versoes de Python compativeis com as dependencias (requirements.txt) ----
REM Hoje quem trava a faixa e o python-rtmidi, que so publica wheel pronto pro Windows
REM ate o Python 3.12 (nada de cp313 ainda). Fora dessa faixa o pip cai pra compilar do
REM zero e falha sem Visual Studio Build Tools instalado. Se uma dependencia futura
REM mudar essa faixa, so ajustar as duas linhas abaixo -- o resto do script se adapta.
set "PY_VERSOES_SUPORTADAS=3.12 3.11 3.10 3.9"
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

REM ---- fluidsynth e ffmpeg: instala via winget se nao estiverem no PATH ----
set "PRECISA_REABRIR_TERMINAL="

where fluidsynth >nul 2>&1
if errorlevel 1 (
    echo [AVISO] fluidsynth nao encontrado no PATH.
    where winget >nul 2>&1
    if not errorlevel 1 (
        echo Instalando fluidsynth via winget...
        winget install --id FluidSynth.FluidSynth -e --silent --accept-source-agreements --accept-package-agreements
        if not errorlevel 1 (
            echo [OK] fluidsynth instalado.
            set "PRECISA_REABRIR_TERMINAL=1"
        ) else (
            echo [ERRO] Falha ao instalar fluidsynth via winget.
        )
    ) else (
        echo [ERRO] winget indisponivel para instalar o fluidsynth.
    )
) else (
    echo [OK] fluidsynth encontrado.
)

where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [AVISO] ffmpeg nao encontrado no PATH.
    where winget >nul 2>&1
    if not errorlevel 1 (
        echo Instalando ffmpeg via winget...
        winget install --id Gyan.FFmpeg -e --silent --accept-source-agreements --accept-package-agreements
        if not errorlevel 1 (
            echo [OK] ffmpeg instalado.
            set "PRECISA_REABRIR_TERMINAL=1"
        ) else (
            echo [ERRO] Falha ao instalar ffmpeg via winget.
        )
    ) else (
        echo [ERRO] winget indisponivel para instalar o ffmpeg.
    )
) else (
    echo [OK] ffmpeg encontrado.
)

REM ---- SoundFont (.sf2): baixa o TimGM6mb (~6MB) se a pasta nao tiver nenhum ----
set "SF2_DIR=midi_game\assets\sf2"
set "SF2_URL=https://raw.githubusercontent.com/craffel/pretty-midi/main/pretty_midi/TimGM6mb.sf2"

dir /b "%SF2_DIR%\*.sf2" >nul 2>&1
if not errorlevel 1 (
    echo [OK] SoundFont ja presente em %SF2_DIR%.
) else (
    echo [AVISO] Nenhum SoundFont ^(.sf2^) encontrado em %SF2_DIR%.
    echo Baixando TimGM6mb.sf2 ^(~6MB, SoundFont GM leve^)...
    if not exist "%SF2_DIR%" mkdir "%SF2_DIR%"
    where curl >nul 2>&1
    if not errorlevel 1 (
        curl -L -o "%SF2_DIR%\TimGM6mb.sf2" "%SF2_URL%"
    ) else (
        powershell -NoProfile -Command "Invoke-WebRequest -Uri '%SF2_URL%' -OutFile '%SF2_DIR%\TimGM6mb.sf2'"
    )
    if exist "%SF2_DIR%\TimGM6mb.sf2" (
        echo [OK] SoundFont baixado com sucesso.
    ) else (
        echo [ERRO] Falha ao baixar o SoundFont automaticamente.
        echo        Baixe manualmente e coloque em: %SF2_DIR%
        echo        Sugestao: TimGM6mb.sf2 ou FluidR3_GM.sf2
    )
)

echo.
where fluidsynth >nul 2>&1
if errorlevel 1 echo [PENDENTE] fluidsynth: instale manualmente -^> https://www.fluidsynth.org/download/ ^(e adicione ao PATH^)
where ffmpeg >nul 2>&1
if errorlevel 1 echo [PENDENTE] ffmpeg: instale manualmente -^> https://ffmpeg.org/download.html ^(e adicione ao PATH^)

if defined PRECISA_REABRIR_TERMINAL (
    echo.
    echo [IMPORTANTE] fluidsynth e/ou ffmpeg foram instalados agora.
    echo              Feche este terminal e abra um novo antes de rodar o jogo,
    echo              para o PATH atualizar.
)

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
