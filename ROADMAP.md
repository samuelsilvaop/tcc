# Roadmap - MIDI Hero

Lista de melhorias planejadas e ideias para trabalhos futuros do projeto.

## Planejado

### Controle de velocidade (andamento) das músicas

Permitir ajustar a velocidade de reprodução de uma música (ex.: 0.75x, 1.0x, 1.25x), útil para praticar trechos rápidos.

- **Notas na tela / pontuação**: mudança simples. `game_engine.py` e a pontuação trabalham sobre tempos absolutos (segundos) derivados do MIDI; basta escalar esses tempos pelo fator de velocidade escolhido (e o `scroll_speed` de `graphics.py`, se quisermos manter a "pista" visual do mesmo tamanho).
- **Áudio**: é a parte mais trabalhosa. O `pygame.mixer.music` não tem controle nativo de velocidade/tempo. Duas abordagens:
  1. **Recomendada**: pré-renderizar variantes de velocidade do `.ogg` usando o filtro `atempo` do ffmpeg (já é dependência do projeto, usado em `audio_converter.py`) — preserva o tom (pitch) da música. Cachear essas variantes do mesmo jeito que o `.ogg` normal já é cacheado hoje.
  2. Alternativa mais simples (mas com trade-off sonoro): tocar o áudio original em velocidade alterada via mudança de sample rate, o que também muda o tom (fica "esganiçado" ou "grave" dependendo da direção) — ou simplesmente mutar o áudio nesse modo (modo prática silencioso).
- **UI**: adicionar seletor de velocidade no menu (`midi_game/menu.py`) e persistir a escolha em `config.json`.

## Melhorias futuras (trabalhos futuros / sugestões de continuidade)

Levantadas na revisão geral do código (2026-07-02). Não são bugs — são pontos de arquitetura/escopo que ficam de fora do projeto atual mas são boas sugestões de continuidade para um TCC futuro:

- **Testes automatizados**: o projeto não tem nenhum teste unitário/integração (ex.: `midi_loader.build_note_spans`, que tem lógica não trivial de casamento `note_on`/`note_off`, seria um bom primeiro alvo).
- **Casamento note_on/note_off em `midi_loader.py`**: hoje é resolvido como pilha (LIFO). Para notas repetidas sem `note_off` entre elas, o `note_off` mais recente fecha o `note_on` mais recente. É uma interpretação válida (o problema é ambíguo por natureza), mas vale documentar a decisão explicitamente ou tornar configurável.
- **Conversão MIDI→OGG sem timeout**: `_render_with_fluidsynth`/ffmpeg em `audio_converter.py` não tem timeout; um MIDI problemático pode travar a inicialização inteira do jogo (a conversão roda antes da janela abrir), sem feedback visual de que algo está acontecendo.
- **Tela de carregamento** durante a conversão MIDI→OGG: na primeira execução, com várias músicas novas, o jogo pode parecer "travado/não abre" enquanto converte tudo em segundo plano sem UI.
- **Encerramento da thread do MIDI listener**: é `daemon=True` e nunca é `join()`ada; ao reiniciar (tecla R) ou trocar de música, portas/threads antigas podem ficar penduradas até o processo terminar. Baixo risco por serem daemon, mas vale revisitar.
- **Acessibilidade**: sem opção para daltonismo (cores verde/vermelho usadas para feedback de teclas), sem remapeamento de teclas de navegação do menu.
- **`README.md` desatualizado**: ainda descreve um fluxo manual de `venv`/`source venv/bin/activate` que não reflete mais o `install.bat`/`Makefile`/`run.bat` já existentes no projeto.
- **Controle de velocidade/andamento das músicas**: ver seção "Planejado" acima.
- **Instalador nativo (setup.exe/MSI)**: hoje a instalação no Windows é feita via `install.bat`, que exige Python no host (ou instala via winget) e baixa fluidsynth/ffmpeg/soundfont da internet a cada setup novo. Uma versão empacotada com PyInstaller (congelando o app, sem depender de Python instalado) e um instalador gerado com Inno Setup ou WiX (MSI) — embutindo fluidsynth/ffmpeg/soundfont no próprio instalador, sem downloads em runtime — daria uma experiência de instalação "duplo-clique" com desinstalador em "Adicionar/Remover Programas". Trade-off: instalador final fica maior (ffmpeg + fluidsynth + soundfont + runtime Python embutido) e passa a exigir um passo extra de build a manter sempre que as dependências nativas mudarem.
