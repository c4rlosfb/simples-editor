# Simples Editor

**Simples Editor** é uma IDE web que permite escrever, compilar e executar programas na linguagem **SIMPLES** diretamente no navegador, sem nenhuma instalação local.

> **Status:** 🚧 Em desenvolvimento inicial — fase de planejamento e documentação. Veja [PROGRESS.md](PROGRESS.md) e [SPRINTS.md](SPRINTS.md) para acompanhar o progresso.

O ambiente planejado conta com três painéis:
- **Editor SIMPLES**: code editor com syntax highlighting das 27 palavras reservadas.
- **Painel NASM x32**: mostra o assembly gerado lado a lado com o código fonte.
- **Terminal interativo**: emulador de terminal (xterm.js) para input/output real via `leia`/`escreva`.

## Documentação

- [PRD — Product Requirements Document](prd-simples-online.md) — Especificação completa (arquitetura, stack, API, segurança, roadmap).
- [SPRINTS.md](SPRINTS.md) — Planejamento dos 6 sprints com entregáveis.
- [PROGRESS.md](PROGRESS.md) — Checklist de progresso por sprint.

## Como começar (Ambiente de Desenvolvimento) 🚧

> As instruções abaixo descrevem o fluxo **planejado** de desenvolvimento local. O `docker compose up` e os serviços ainda não estão implementados — aguardando Sprint 1.

### Pré-requisitos (planejados)
- Docker Engine 24+ ou Docker Desktop
- Docker Compose v2
- Conta no Supabase (para gerenciar a autenticação)

### Passo a passo (planejado)

1. Clone o repositório (com submodules):
   ```bash
   git clone --recurse-submodules https://github.com/c4rlosfb/simples-editor.git
   cd simples-editor
   ```

2. Configure as variáveis de ambiente:
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas credenciais do Supabase
   ```

3. Suba os containers:
   ```bash
   docker compose up --build -d
   ```

4. Acesse no navegador:
   - Frontend: `http://localhost`
   - Backend health check: `http://localhost/api/health`

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | React + TanStack Start + Monaco Editor + xterm.js + Tailwind |
| Backend | Python (Flask + flask-sock + docker SDK) |
| Sandbox | Docker descartável com `qemu-user-static` (roda binários x86 em ARM64) |
| Infra | Docker Compose + Nginx reverse proxy + Oracle Cloud Ampere A1 (Always Free) |
| Auth | Supabase (JWT) |
