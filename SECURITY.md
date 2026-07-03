# Política de Segurança

Este é um projeto pessoal de TCC (MIDI Hero), sem infraestrutura de produção
ou dados de terceiros — mas segue boas práticas de segurança por padrão.

## Reportar uma vulnerabilidade

Não abra issue pública para vulnerabilidades. Reporte de forma privada:

- Use **GitHub Security Advisories** (aba *Security* → *Report a vulnerability*), ou
- e-mail para `samuelsilvaop@gmail.com`.

Inclua: descrição, passos para reproduzir, impacto e versão afetada.

## Práticas adotadas neste projeto

- Dependências (`requirements.txt`) e GitHub Actions pinadas (versão exata / SHA),
  com atualização via Dependabot.
- CI de segurança bloqueante (`.github/workflows/security.yml`): secret scanning,
  CodeQL (SAST), scan de vulnerabilidades em dependências e checagem de licenças.
- Pre-commit com Gitleaks para barrar segredos antes do commit.
- Sem coleta de dados pessoais: o jogo roda localmente e só grava progresso/config
  (`save_data.json`, `config.json`) na máquina do próprio jogador.
