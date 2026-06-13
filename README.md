# Simples Editor

> **Web IDE para a linguagem SIMPLES — disciplina de Compiladores**
>
> [![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)](PROGRESS.md)
> [![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**Simples Editor** é uma IDE web que permite escrever, compilar e executar programas na linguagem **SIMPLES** diretamente no navegador, sem nenhuma instalação local.

---

## 🖥️ Interface

```
┌──────────────────────────────────────────────────────────────────────┐
│  HEADER:  Simples Editor                     [usuario@email] [Sair]  │
├──────────────────────────────────────────────────────────────────────┤
│  TOOLBAR:  [▶ Run]  [■ Stop]  [Limpar]        [exemplos ▾]          │
├───────────────────────────────┬──────────────────────────────────────┤
│                               │  NASM x86 (Assembly)                 │
│  Editor SIMPLES (Monaco)      │  ┌────────────────────────────────┐  │
│  ┌─────────────────────────┐  │  │ section .bss                   │  │
│  │ programa exemplo        │  │  │     x resd 1                   │  │
│  │   inteiro x             │  │  │                                │  │
│  │ inicio                  │  │  │ section .text                  │  │
│  │   leia x                │  │  │     global _start              │  │
│  │   escreva x             │  │  │ _start:                        │  │
│  │ fim                     │  │  │     mov eax, 3                 │  │
│  └─────────────────────────┘  │  │     int 0x80                   │  │
│                               │  └────────────────────────────────┘  │
├───────────────────────────────┴──────────────────────────────────────┤
│  Terminal (xterm.js)                        [exit code: 0 — 0.18s]   │
│  $ Digite um numero: 42                                              │
│  42                                                                  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Arquitetura

```
┌──────────────────────────────────────────────────────────────────┐
│                        Cliente (Browser)                           │
│  React + Monaco Editor + xterm.js                                  │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTPS / WSS
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Nginx (reverse proxy)                          │
│  TLS termination  ·  WebSocket upgrade  ·  static files            │
└──────────────┬───────────────────────────────┬───────────────────┘
               │                               │
        ┌──────▼──────┐                 ┌──────▼──────────────┐
        │  Frontend    │                 │  Backend (Flask)     │
        │  (static)    │                 │  simplesc → nasm → ld│
        └──────────────┘                 │  Docker SDK           │
                                         └──────┬───────────────┘
                                                │ docker run --rm
                                                │ --network=none
                                                ▼
                                         ┌──────────────────────┐
                                         │  Sandbox Docker       │
                                         │  qemu-i386-static     │
                                         │  binário ELF i386     │
                                         └──────────────────────┘

External:  Supabase (Auth)
```

---

## 🚀 Pipeline de Compilação

```
Código SIMPLES  ──→  simplesc  ──→  NASM  ──→  ld  ──→  Binário ELF i386
      │                (C99)        (elf32)     (elf_i386)        │
      │                  │             │            │             │
      │            timeout 15s   timeout 15s  timeout 15s         │
      │                                                           ▼
      │                                                  ┌────────────────┐
      └── Erro: {line, column, message, phase} ←────────│ Docker Sandbox  │
                                                         │ qemu-i386       │
                                                         │ --cap-drop=ALL  │
                                                         │ --network=none  │
                                                         │ --memory=128m   │
                                                         └────────────────┘
```

---

## 📦 Stack

| Camada | Tecnologia |
|---|---|
| **Frontend** | React 18 · TanStack Start · Monaco Editor · xterm.js · Tailwind CSS |
| **Backend** | Python 3.11 · Flask · flask-sock · Gunicorn + gevent |
| **Compilador** | simplesc (C99) · NASM 2.15+ · binutils-i686-linux-gnu |
| **Sandbox** | Docker · qemu-user-static · cgroups · seccomp |
| **Infra** | Docker Compose · Nginx · Oracle Cloud Ampere A1 (ARM64 Always Free) |
| **Auth** | Supabase (JWT · RS256/HS256) |
| **Observabilidade** | structlog (JSON) · Prometheus · pytest |

---

## 📁 Estrutura do Projeto

```
simples-editor/
├── backend/
│   ├── app.py              # Flask API (health, compile, limits)
│   ├── auth.py             # @verify_jwt decorator + JWT validation
│   ├── config.py           # Config via env vars (dataclass)
│   ├── compiler.py         # Serviço de compilação (simplesc wrapper)
│   ├── linker.py           # Linker cross-target (i686-linux-gnu-ld)
│   ├── pipeline.py         # Pipeline completo com timeouts por estágio
│   ├── supabase_client.py  # Cliente Supabase (singleton)
│   ├── Dockerfile          # Multi-stage: ubuntu + nasm + binutils
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── routes/         # Rotas TanStack Router (/, /login)
│   │   ├── components/     # LoginPage, SimplesEditor, NasmPanel, TerminalPanel
│   │   └── lib/            # supabase.ts, simples-monarch.ts, simples-language.ts
│   ├── app.config.ts       # Config TanStack Start
│   └── package.json
├── terraform/              # Provisionamento OCI Ampere A1
│   ├── main.tf
│   └── cloud-init.yaml
├── tests/                  # Testes unitários (pytest)
├── e2e/                    # Testes E2E (Playwright)
├── docs/                   # Documentação
├── docker-compose.yml
├── prd-simples-online.md   # PRD completo (1630 linhas)
├── SPRINTS.md              # Planejamento dos 6 sprints
└── PROGRESS.md             # Checklist de progresso
```

---

## 🛠️ Desenvolvimento Local

### Pré-requisitos

- Docker Engine 24+ ou Docker Desktop
- Docker Compose v2
- Conta no [Supabase](https://supabase.com) (free tier)

### Setup

```bash
# 1. Clone
git clone --recurse-submodules https://github.com/c4rlosfb/simples-editor.git
cd simples-editor

# 2. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_JWT_SECRET

# 3. Suba os containers
docker compose up --build -d

# 4. Acesse
# Frontend: http://localhost
# Health:   http://localhost/api/health
```

### Testes

```bash
# Backend (pytest)
cd backend && pytest tests/ -v

# Frontend (Playwright E2E)
cd e2e && npm test
```

---

## ☁️ Deploy (Oracle Cloud)

Provisionamento automatizado via Terraform para **OCI Ampere A1** (Always Free: 4 OCPU / 24 GB RAM).

```bash
cd terraform
terraform init
terraform plan  -var-file="oci.tfvars"
terraform apply -var-file="oci.tfvars"
```

Ver [terraform/README.md](terraform/README.md) para instruções completas de deploy e TLS.

---

## 📚 Documentação

| Documento | Descrição |
|---|---|
| [PRD](prd-simples-online.md) | Product Requirements Document — arquitetura, API, segurança, roadmap |
| [SPRINTS.md](SPRINTS.md) | Planejamento dos 6 sprints com entregáveis |
| [PROGRESS.md](PROGRESS.md) | Checklist de progresso por sprint |
| [DOMAIN.md](DOMAIN.md) | Guia de configuração de domínio próprio + TLS |
| [PRESENTATION.md](PRESENTATION.md) | Slide deck da apresentação final (Marp) |

---

## 🔒 Segurança

- **9 camadas de sandbox**: `--network=none` · `--cap-drop=ALL` · `--read-only` · `--memory=128m` · `--pids-limit=64` · non-root · seccomp · timeouts · rate limit
- **Autenticação**: JWT via Supabase com JWKS (RS256) + fallback HMAC (HS256)
- **Timeouts**: 3 camadas (compile 15s, wall-clock 10s, Docker hard stop 12s)
- **Rate limit**: 30 execuções/minuto por usuário

---

## 👥 Equipe

| Integrante | GitHub |
|---|---|
| Carlos Barbosa | [@c4rlosfb](https://github.com/c4rlosfb) |
| Luan Cas Dias | [@LuanCasDias](https://github.com/LuanCasDias) |
| Kauã | [@KauaN-png](https://github.com/KauaN-png) |

**IFSULDEMINAS — Campus Poços de Caldas — Engenharia de Computação — Disciplina de Compiladores**
