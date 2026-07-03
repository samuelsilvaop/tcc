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

REM Atualiza o PATH desta janela com o valor que o instalador do winget acabou
REM de gravar no registro -- assim nao precisa fechar/reabrir o terminal so pra
REM o "py"/"python" novo aparecer.
call :refrescar_path

py -%PY_RECOMENDADA% --version >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Python foi instalado, mas nao foi reconhecido nesta janela
    echo         mesmo apos atualizar o PATH. Feche este terminal, abra um novo
    echo         e rode install.bat de novo.
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
echo %CD% | findstr /I "OneDrive" >nul
if not errorlevel 1 (
    echo [AVISO] Esta pasta esta dentro do OneDrive. A sincronizacao do OneDrive
    echo         costuma deixar a instalacao bem mais lenta ^(pode parecer travado
    echo         por varios minutos, principalmente no passo "Installing collected
    echo         packages"^). Isso e normal nessa condicao -- so aguarde terminar.
    echo         Se puder, mova a pasta do jogo para fora do OneDrive ^(ex: C:\MidiHero^)
    echo         para acelerar.
    echo.
)
REM pip nao consegue substituir o proprio pip.exe em execucao no Windows -- por
REM isso o upgrade tem que ser feito via "python -m pip", nunca via "pip install
REM --upgrade pip" direto (senao da erro "To modify pip, please run...").
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo === Dependencias Python instaladas com sucesso! ===
echo.

REM ---- Visual C++ Redistributable: dependencia nativa de extensoes compiladas
REM como o python-rtmidi. Sem isso, "import rtmidi" quebra com "DLL load failed".
if not exist "%WINDIR%\System32\vcruntime140.dll" (
    echo [AVISO] Microsoft Visual C++ Redistributable nao encontrado.
    where winget >nul 2>&1
    if not errorlevel 1 (
        echo Instalando Visual C++ Redistributable via winget...
        winget install --id Microsoft.VCRedist.2015+.x64 -e --silent --accept-source-agreements --accept-package-agreements
        if not errorlevel 1 (
            echo [OK] Visual C++ Redistributable instalado.
        ) else (
            echo [ERRO] Falha ao instalar via winget.
            echo        Baixe manualmente em: https://aka.ms/vs/17/release/vc_redist.x64.exe
        )
    ) else (
        echo [ERRO] winget indisponivel para instalar o Visual C++ Redistributable.
        echo        Baixe manualmente em: https://aka.ms/vs/17/release/vc_redist.x64.exe
    )
) else (
    echo [OK] Visual C++ Redistributable encontrado.
)

REM ---- fluidsynth: nao existe pacote winget oficial pra isso, entao baixamos o
REM build oficial (zip autocontido, sem instalador) do GitHub Releases e
REM extraimos dentro do proprio projeto, em tools\fluidsynth\bin.
set "PRECISA_REABRIR_TERMINAL="
set "FLUIDSYNTH_DIR=tools\fluidsynth"
set "FLUIDSYNTH_ZIP_URL=https://github.com/FluidSynth/fluidsynth/releases/download/v2.5.5/fluidsynth-v2.5.5-win10-x64-cpp11.zip"

where fluidsynth >nul 2>&1
if not errorlevel 1 (
    echo [OK] fluidsynth encontrado no PATH.
) else if exist "%FLUIDSYNTH_DIR%\bin\fluidsynth.exe" (
    echo [OK] fluidsynth ja baixado em %FLUIDSYNTH_DIR%.
) else (
    echo [AVISO] fluidsynth nao encontrado. Baixando build oficial...
    set "FLUIDSYNTH_ZIP=%TEMP%\fluidsynth.zip"
    where curl >nul 2>&1
    if not errorlevel 1 (
        curl -L -o "!FLUIDSYNTH_ZIP!" "%FLUIDSYNTH_ZIP_URL%"
    ) else (
        powershell -NoProfile -Command "Invoke-WebRequest -Uri '%FLUIDSYNTH_ZIP_URL%' -OutFile '!FLUIDSYNTH_ZIP!'"
    )
    if exist "!FLUIDSYNTH_ZIP!" (
        if exist "%FLUIDSYNTH_DIR%_tmp" rmdir /s /q "%FLUIDSYNTH_DIR%_tmp"
        powershell -NoProfile -Command "Expand-Archive -Path '!FLUIDSYNTH_ZIP!' -DestinationPath '%FLUIDSYNTH_DIR%_tmp' -Force"
        set "FS_EXTRAIDO="
        for /d %%D in ("%FLUIDSYNTH_DIR%_tmp\*") do set "FS_EXTRAIDO=%%D"
        if defined FS_EXTRAIDO (
            if exist "%FLUIDSYNTH_DIR%" rmdir /s /q "%FLUIDSYNTH_DIR%"
            move "!FS_EXTRAIDO!" "%FLUIDSYNTH_DIR%" >nul
        )
        rmdir /s /q "%FLUIDSYNTH_DIR%_tmp" 2>nul
        del /q "!FLUIDSYNTH_ZIP!" 2>nul
    )
    if exist "%FLUIDSYNTH_DIR%\bin\fluidsynth.exe" (
        echo [OK] fluidsynth baixado com sucesso em %FLUIDSYNTH_DIR%.
    ) else (
        echo [ERRO] Falha ao baixar/extrair o fluidsynth automaticamente.
        echo        Baixe manualmente em: https://github.com/FluidSynth/fluidsynth/releases
        echo        e extraia de forma que exista: %FLUIDSYNTH_DIR%\bin\fluidsynth.exe
    )
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
            call :refrescar_path
            where ffmpeg >nul 2>&1
            if errorlevel 1 set "PRECISA_REABRIR_TERMINAL=1"
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
if errorlevel 1 if not exist "%FLUIDSYNTH_DIR%\bin\fluidsynth.exe" echo [PENDENTE] fluidsynth: instale manualmente -^> https://github.com/FluidSynth/fluidsynth/releases
where ffmpeg >nul 2>&1
if errorlevel 1 echo [PENDENTE] ffmpeg: instale manualmente -^> https://ffmpeg.org/download.html ^(e adicione ao PATH^)

if defined PRECISA_REABRIR_TERMINAL (
    echo.
    echo [IMPORTANTE] ffmpeg foi instalado agora via winget.
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
goto :eof

REM ---- Recarrega o PATH desta janela a partir do registro (Machine + User),
REM igual o Windows faria ao abrir um terminal novo. Usado depois de instalar
REM algo via winget para nao depender do usuario fechar/reabrir o terminal.
:refrescar_path
set "PATH_SISTEMA="
set "PATH_USUARIO="
for /f "tokens=2,*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "PATH_SISTEMA=%%B"
for /f "tokens=2,*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "PATH_USUARIO=%%B"
set "PATH=%PATH_SISTEMA%;%PATH_USUARIO%;%PATH%"
exit /b 0
