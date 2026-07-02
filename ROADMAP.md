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
- **Combo/streak no HUD**: contador de acertos consecutivos (zera em miss ou tecla errada), exibido ao lado do "Pontos:" em `_draw_hud()`. A infraestrutura de detecção já existe (hit/miss/tecla errada em `main.py`), só falta um contador e a UI — motivador comum em jogos de ritmo que hoje falta aqui (o jogador só sabe como foi no final).
- **Instalador nativo (setup.exe/MSI)**: hoje a instalação no Windows é feita via `install.bat`, que exige Python no host (ou instala via winget) e baixa fluidsynth/ffmpeg/soundfont da internet a cada setup novo. Uma versão empacotada com PyInstaller (congelando o app, sem depender de Python instalado) e um instalador gerado com Inno Setup ou WiX (MSI) — embutindo fluidsynth/ffmpeg/soundfont no próprio instalador, sem downloads em runtime — daria uma experiência de instalação "duplo-clique" com desinstalador em "Adicionar/Remover Programas". Trade-off: instalador final fica maior (ffmpeg + fluidsynth + soundfont + runtime Python embutido) e passa a exigir um passo extra de build a manter sempre que as dependências nativas mudarem.
- **Front-end web (JS/Phaser) mantendo o back-end Python**: se no futuro quisermos um visual mais bonito/polido sem reescrever o motor, a ideia é dividir em duas etapas em vez de portar tudo pra Unity/Unreal: Python continua responsável pela parte difícil e já resolvida (entrada MIDI de teclado físico em tempo real via `mido`/`python-rtmidi`, sincronia áudio/vídeo, geração dos spans de nota a partir do `.mid`), exportando os dados de timing em JSON; um front-end em JS (Phaser/PixiJS + Web Audio API) assume só a renderização/animação das notas caindo e efeitos visuais. Justificativa: o desafio técnico central deste projeto sempre foi a sincronia de input MIDI ao vivo + áudio (ver histórico de commits: race condition, dessincronia, engate tardio), não a estética das barras — nem Unity (precisa de plugin de terceiros pra MIDI ao vivo, não é nativo) nem JS puro (Web MIDI API existe, mas a latência de áudio polifônico varia entre navegadores) resolvem essa parte de graça. Reescrever o motor do zero significaria resolver de novo um problema já resolvido, só pra ganhar visual — por isso a recomendação é manter Python como o "motor" e tratar um front-end web como camada cosmética opcional, não como substituição.
