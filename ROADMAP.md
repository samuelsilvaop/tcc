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

_(a preencher após a revisão geral do projeto)_
