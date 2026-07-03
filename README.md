# MIDI Hero

Um jogo de ritmo estilo Guitar Hero, mas tocado com um teclado musical MIDI de
verdade: as notas de qualquer arquivo `.mid` caem na tela e você as acerta
apertando as teclas correspondentes no seu teclado/piano MIDI conectado.

Projeto desenvolvido como TCC — o desafio técnico central é a sincronia entre
entrada MIDI ao vivo (via `mido`/`python-rtmidi`) e a reprodução de áudio,
não a estética das barras caindo. Veja [ROADMAP.md](ROADMAP.md) para
detalhes de arquitetura, decisões de projeto e ideias de continuidade.

## Requisitos

- Um teclado/piano MIDI (USB ou com interface MIDI) conectado ao computador.
- Python 3.9–3.13 (3.12 recomendado — veja a nota sobre versões abaixo).
- [ffmpeg](https://ffmpeg.org/) e [FluidSynth](https://www.fluidsynth.org/),
  usados para converter os `.mid` em áudio (`.ogg`) na primeira execução.
- Um SoundFont (`.sf2`) em `midi_game/assets/sf2/` — o instalador baixa um
  automaticamente (TimGM6mb, leve) se a pasta estiver vazia.

> **Nota sobre versão do Python:** o `python-rtmidi` só publica wheel pronta
> para Windows até o Python 3.12 (sem isso, o `pip install` cai para compilar
> do zero e falha sem as Build Tools do Visual Studio). No Linux/macOS, o
> `pygame` 2.6.1 tem um bug de import circular em Python 3.14+. Por isso o
> instalador prioriza automaticamente uma versão dentro dessa faixa, e se
> nenhuma estiver instalada ele se oferece para instalar uma (ver abaixo).

## Instalação

### Windows

```
install.bat
```

Cria o ambiente virtual, instala as dependências Python e tenta resolver
automaticamente (via [winget](https://learn.microsoft.com/windows/package-manager/winget/))
o que faltar: Python 3.12, Visual C++ Redistributable e ffmpeg. O FluidSynth
é baixado como build oficial (zip autocontido) direto para dentro do
projeto, em `tools/fluidsynth/`. O SoundFont é baixado automaticamente.

### Linux / macOS

```
make install
```

Cria o ambiente virtual (`.venv`) e instala as dependências Python. Também
verifica as dependências de sistema e se oferece para instalar
automaticamente o que faltar — **cada instalação pede confirmação antes de
agir** (nada é instalado sem você autorizar):

- **Homebrew** (só no macOS, se ainda não estiver instalado).
- **Python** numa versão compatível (3.9–3.13), via `brew`/`apt`/`dnf`/`pacman`,
  caso nenhuma já esteja presente no sistema.
- **FluidSynth** e **ffmpeg**, via o gerenciador de pacotes detectado
  (`pacman`, `apt-get`, `dnf` ou `brew`).

No Arch/Manjaro o `pacman` só mantém a versão mais recente do Python nos
repositórios oficiais, que pode estar fora da faixa suportada — nesse caso o
instalador avisa e recomenda uma instalação manual (ex.: via `pyenv`).

Se preferir escolher seu próprio SoundFont, coloque um `.sf2` em
`midi_game/assets/sf2/` antes de rodar `make install` (senão o instalador
baixa um automaticamente).

## Executando o jogo

- **Windows:** `run.bat`
- **Linux/macOS:** `make run`

Na primeira execução, o jogo converte os `.mid` de `midi_game/assets/midi/`
para `.ogg` (cacheado depois, então execuções seguintes são instantâneas) e
depois mostra o menu para escolher a música e configurar o teclado MIDI
(porta, quantidade de teclas, nota mais grave etc. — tudo salvo em
`midi_game/config.json`).

## Controles

**Menu:** setas / `WASD` para navegar, `Enter` para confirmar, `Esc` para
voltar/sair.

**Durante a música:** as notas caem na pista e você acerta apertando a tecla
correspondente no seu teclado MIDI físico — não há input pelo teclado do
computador para tocar.

**Tela de resultado:**
- `Enter` — voltar ao menu
- `R` — jogar a mesma música de novo
- `Esc` — sair

Seus recordes por música ficam salvos em `midi_game/save_data.json`.

## Desinstalando

- **Windows:** `uninstall.bat`
- **Linux/macOS:** `make uninstall`

Remove o ambiente virtual, cache Python, SoundFont baixado e os dados
salvos (progresso/configuração) deste projeto. Cada etapa pede confirmação
antes de agir, e a remoção de softwares de sistema (Python, ffmpeg,
FluidSynth, Visual C++ Redistributable) é sempre opcional e avisada
separadamente, já que esses programas podem estar em uso por outros
aplicativos do seu computador.

## Estrutura do projeto

```
main.py                    # loop principal do jogo
midi_game/
  assets/midi/              # arquivos .mid das músicas
  assets/sf2/                # SoundFont (.sf2), não versionado
  audio_converter.py         # conversão .mid -> .ogg via FluidSynth/ffmpeg
  config.py                  # config.json (porta MIDI, volume, teclas...)
  game_engine.py              # lógica de spans de nota / pontuação
  graphics.py                 # renderização (pygame)
  live_monitor.py              # síntese do teclado MIDI ao vivo
  menu.py                       # menus (seleção de música, config)
  midi_input.py                  # leitura da porta MIDI em tempo real
  midi_loader.py                   # parsing do .mid em spans de nota
  save_data.py                      # save_data.json (recordes por música)
monografia/                # TCC (LaTeX)
```

## Licença

Distribuído sob a licença MIT — veja [LICENSE](LICENSE).
