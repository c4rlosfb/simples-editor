# Simples Editor

<p align="center">
  <img src="https://img.shields.io/badge/status-em%20desenvolvimento-yellow?style=for-the-badge" alt="Status: Em Desenvolvimento" />
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" alt="License: MIT" />
  <img src="https://img.shields.io/badge/stack-React%20%7C%20Flask%20%7C%20Docker-0b3b60?style=for-the-badge" alt="Stack: React, Flask, Docker" />
  <img src="https://img.shields.io/badge/deploy-Oracle%20Cloud%20Ampere%20A1-f80000?style=for-the-badge&logo=oracle" alt="Deploy: Oracle Cloud ARM64" />
</p>

---

> **Web IDE para a linguagem SIMPLES** — escreva, compile e execute código SIMPLES diretamente no navegador, com visualização lado-a-lado do assembly gerado e terminal interativo real. Projeto acadêmico da disciplina de **Compiladores** do [IFSULDEMINAS — Campus Poços de Caldas](https://portal.pcs.ifsuldeminas.edu.br/).

---

## Visão Geral

O **Simples Editor** elimina a fricção de configurar toolchain local para a disciplina de Compiladores. O aluno acessa a IDE web, autentica, escreve código na linguagem didática **SIMPLES** (27 palavras reservadas em português estruturado) e com um clique vê:

1. O **assembly NASM x86 32-bit** gerado pelo compilador, lado-a-lado com o código fonte.
2. A **execução real** do binário em um terminal interativo no navegador — suporte completo a `leia` (stdin) e `escreva` (stdout).
3. **Erros de compilação** destacados diretamente no editor, com linha e coluna.

Tudo roda em containers Docker descartáveis, com 9 camadas de isolamento, sem rede e com timeouts automáticos — o aluno experimenta sem medo de travar o serviço para os colegas.

---

## Interface

```
┌──────────────────────────────────────────────────────────────────────────┐
│  HEADER:  Simples Editor                [aluno@email.com]      [Sair]    │
├──────────────────────────────────────────────────────────────────────────┤
│  TOOLBAR:  [▶ Run]   [■ Stop]   [Limpar]          [exemplos ▾]          │
├────────────────────────────────┬─────────────────────────────────────────┤
│                                │                                         │
│   EDITOR (Monaco)              │  NASM x86 32-bit (read-only)            │
│   ─────────────────────        │  ───────────────────────────            │
│   programa exemplo             │  section .bss                           │
│     inteiro x                  │      x resd 1                           │
│   inicio                       │                                         │
│     leia x                     │  section .text                          │
│     escreva x                  │      global _start                      │
│   fim                          │  _start:                                │
│                                │      mov eax, 3                         │
│                                │      mov ebx, 0                         │
│                                │      mov ecx, x                         │
│                                │      mov edx, 4                         │
│                                │      int 0x80                           │
│                                │      ...                                │
│                                │                                         │
├────────────────────────────────┴─────────────────────────────────────────┤
│  TERMINAL (xterm.js)                                   [⌃C interrompe]   │
│  ─────────────────────────────────────────────────────────────────────── │
│  Digite um numero: 42                                                     │
│  42                                                                       │
│                                                                           │
│  [exit code: 0 — 0.18s]                                                   │
└──────────────────────────────────────────────────────────────────────────┘
```

**3 painéis, 2 splitters arrastáveis:**
- **Splitter vertical** entre Editor SIMPLES (esquerda) e NASM (direita) — double-click colapsa/restaura o painel NASM.
- **Splitter horizontal** entre área de código (superior) e Terminal (inferior).

---

## Arquitetura

```
                        ┌──────────────────────────┐
                        │   Cliente (Browser)       │
                        │   React + TanStack Start  │
                        │   ┌─────────┐┌──────────┐ │
                        │   │ Monaco  ││ NASM     │ │
                        │   │ SIMPLES ││ viewer   │ │
                        │   └─────────┘└──────────┘ │
                        │   ┌──────────────────────┐ │
                        │   │ xterm.js (terminal)  │ │
                        │   └──────────────────────┘ │
                        └───────┬──────────┬─────────┘
                                │ HTTPS    │ WSS
                                ▼          ▼
                        ┌──────────────────────────┐
                        │   Nginx (reverse proxy)   │
                        │   TLS + WebSocket upgrade │
                        └───────┬──────────┬─────────┘
                                │          │
                    ┌───────────▼──┐  ┌────▼──────────────┐
                    │  Frontend    │  │  Backend           │
                    │  (estático)  │  │  Flask + flask-sock│
                    │  nginx:alp   │  │  asyncio + docker  │
                    └──────────────┘  │  + simplesc        │
                                      │  + nasm + ld       │
                                      │  + ptyprocess      │
                                      └────────┬───────────┘
                                               │ docker run --rm
                                               │ --network=none
                                               │ --read-only
                                               ▼
                                      ┌────────────────────┐
                                      │  Sandbox container  │
                                      │  simples-runner     │
                                      │  qemu-i386-static   │
                                      │  (emula x86 32-bit  │
                                      │   em hosts ARM64)   │
                                      └────────────────────┘
          ┌─────────────────┐
          │   Supabase      │
          │   (Auth cloud)  │
          └─────────────────┘
```

### Componentes

| Componente | Tecnologia | Responsabilidade |
|---|---|---|
| **Frontend** | React 18, TanStack Start, Monaco Editor, xterm.js | UI da IDE, edição de código, destaque de sintaxe, terminal interativo, autenticação |
| **Backend** | Python 3.11+, Flask, flask-sock, docker SDK | Orquestração do pipeline de compilação, bridge WebSocket↔PTY, gerenciamento de sandboxes |
| **Nginx** | Nginx 1.25+ Alpine | Reverse proxy HTTPS/WSS, TLS termination, sticky session |
| **Sandbox** | qemu-user-static, Docker | Execução isolada dos binários compilados — sem rede, sem root, sem FS gravável |
| **Auth** | Supabase (cloud free tier) | Autenticação JWT — sem banco local em v1 |

### Padrões de Projeto

| Padrão | Aplicação |
|---|---|
| **Strategy** | `PtyExecutionStrategy` — troca modo de execução (PTY vs batch) sem alterar pipeline |
| **Façade** | `CompilerService.compile_and_run()` — esconde orquestração `simplesc → nasm → ld → docker` |
| **Factory** | `SandboxFactory.create()` — centraliza criação de containers com limites consistentes |
| **Observer** | Eventos WebSocket (`compile_started`, `asm_generated`, `stdout`, `exit`) — frontend reage sem polling |
| **Command** | Mensagens tipadas no protocolo WS (`compile_and_run`, `stdin`, `stop`) |

---

## Pipeline de Compilação

```
Código SIMPLES ──▶ simplesc (C99) ──▶ NASM .asm ──▶ nasm -f elf32 ──▶ .o
                                                                       │
                                                              ld -m elf_i386
                                                                       │
                                                                       ▼
                                                               Binário ELF i386
                                                                       │
                                                    ┌──────────────────┘
                                                    ▼
                                         Docker Sandbox descartável
                                         qemu-i386-static /sandbox/prog
                                                    │
                                         ┌──────────┴──────────┐
                                         ▼                      ▼
                                    stdout/stderr            stdin
                                         │                      │
                                         └──────────┬───────────┘
                                                    ▼
                                          xterm.js (navegador)
```

**Fases com timeouts independentes:**
1. **Compilação** (`simplesc`): 15s
2. **Montagem** (`nasm -f elf32`): 15s
3. **Linkagem** (`ld -m elf_i386`): 15s
4. **Execução wall-clock**: 10s (soft) + 12s (hard limit Docker)

> O compilador `simplesc` usa `binutils-i686-linux-gnu` para cross-linkagem i386 em qualquer arquitetura de host (x86_64 ou ARM64). A execução usa `qemu-user-static` para emular binários x86 32-bit em hosts ARM64 (Oracle Cloud Ampere A1).

---

## Stack Tecnológica

### Frontend

| Tecnologia | Versão | Descrição |
|---|---|---|
| React | 18.x | Biblioteca UI |
| TypeScript | 5.x | Tipagem estática |
| TanStack Start | latest | Framework full-stack React |
| TanStack Query | 5.x | Gerenciamento de estado assíncrono |
| TanStack Router | 1.x | Roteamento tipado |
| Tailwind CSS | 3.x | Estilização utility-first |
| Monaco Editor | `@monaco-editor/react` | Editor de código (mesmo núcleo do VS Code) |
| xterm.js | 5.x | Emulador de terminal |
| xterm-addon-fit | latest | Resize dinâmico do terminal |
| react-resizable-panels | latest | Splitters arrastáveis |
| @supabase/supabase-js | 2.x | Cliente de autenticação |
| @supabase/auth-ui-react | latest | UI de login pronta |

### Backend

| Tecnologia | Versão | Descrição |
|---|---|---|
| Python | 3.11+ | Linguagem do backend |
| Flask | 3.x | API REST |
| flask-sock | latest | WebSocket sobre Flask |
| gevent | 23.x | Worker assíncrono para WS |
| docker SDK | 7.x | Spawn de containers sandbox |
| PyJWT | 2.x | Validação de tokens Supabase |
| structlog | 24.x | Logs estruturados JSON |
| prometheus-client | latest | Métricas em `/metrics` |
| flask-limiter | latest | Rate limiting |
| pytest | 8.x | Testes automatizados |

### Toolchain de Compilação

| Ferramenta | Descrição |
|---|---|
| `simplesc` | Compilador SIMPLES → NASM (C99, já existente) |
| NASM 2.15+ | Assembler x86 (cross-platform) |
| binutils-i686-linux-gnu | Cross-linker i386 (`i686-linux-gnu-ld`) |
| qemu-user-static | Emulação user-mode x86 32-bit em ARM64 |

### Infraestrutura

| Tecnologia | Descrição |
|---|---|
| Docker 24+ | Containerização e sandbox |
| Docker Compose v2 | Orquestração local e produção |
| Nginx 1.25 | Reverse proxy + TLS |
| Supabase (cloud) | Autenticação JWT |
| Oracle Cloud Ampere A1 | Deploy ARM64 Always Free |

---

## Estrutura do Projeto

```
simples-editor/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   └── feature.md          # Template de issue para features
│   └── pull_request_template.md
├── frontend/                    # ⚛️  React + TanStack Start
│   ├── src/
│   │   ├── components/          # Componentes React (Editor, NASM, Terminal)
│   │   ├── routes/              # Rotas da aplicação
│   │   └── lib/                 # Clientes (Supabase, WebSocket)
│   ├── Dockerfile
│   └── nginx-static.conf
├── backend/                     # 🐍  Flask + WebSocket
│   ├── app/
│   │   ├── auth/                # Decorator @verify_jwt
│   │   ├── compiler/            # Façade CompilerService
│   │   ├── executor/            # PtyExecutionStrategy, SandboxFactory
│   │   └── ws/                  # Handlers WebSocket
│   ├── simples-compiler/        # Submódulo: código fonte do simplesc
│   ├── requirements.txt
│   └── Dockerfile
├── runner/                      # 🏃  Imagem do sandbox
│   └── Dockerfile               # debian:12-slim + qemu-user-static
├── nginx/                       # 🔀  Reverse proxy
│   ├── nginx.conf
│   └── certs/                   # TLS (gerado pelo certbot)
├── terraform/                   # 🏗️  IaC Oracle Cloud
│   ├── main.tf
│   ├── variables.tf
│   └── cloud-init.yaml
├── docker-compose.yml           # Stack completa
├── .env.example                 # Template de variáveis de ambiente
├── README.md                    # 📖  Este documento
├── PRD.md                       # 📋  Product Requirements Document
├── SPRINTS.md                   # 🏃  Planejamento de sprints
├── PROGRESS.md                  # ✅  Acompanhamento de tarefas
├── RETROSPECTIVE.md             # 🔄  Retrospectiva da equipe
├── DOMAIN.md                    # 🌐  Guia de domínio próprio + TLS
├── PRESENTATION.md              # 🎤  Slides Marp para apresentação
└── LICENSE                      # MIT
```

---

## Como Rodar Localmente

### Pré-requisitos

- **Docker Engine 24+** (ou Docker Desktop)
- **Docker Compose v2**
- Conta no [Supabase](https://supabase.com) (free tier) com projeto criado
- Git (para clonar com submódulos)

> Funciona em: Linux x86_64, macOS (Intel e Apple Silicon), Windows com WSL2.

### Passo a passo

```bash
# 1. Clone o repositório com submódulos
git clone --recurse-submodules https://github.com/c4rlosfb/simples-editor.git
cd simples-editor

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com:
#   SUPABASE_URL=https://<seu-projeto>.supabase.co
#   SUPABASE_ANON_KEY=<sua-anon-key>
#   SUPABASE_JWT_SECRET=<seu-jwt-secret>

# 3. Suba todos os serviços
docker compose up --build -d

# 4. Verifique
curl http://localhost/api/health
# → {"status":"ok","version":"1.0.0"}

# 5. Acesse no navegador
# http://localhost
```

### Comandos úteis

```bash
docker compose ps                  # Status de todos os serviços
docker compose logs -f backend     # Logs do backend em tempo real
docker compose down                # Derruba tudo
docker compose up --build -d       # Reconstrói e sobe
```

---

## Deploy (Oracle Cloud Ampere A1)

O deploy de produção é feito na **Oracle Cloud Infrastructure**, usando instâncias **Ampere A1 (ARM64)** do tier **Always Free**: 4 OCPUs, 24 GB RAM, 200 GB storage — sem custo.

### 1. Provisionar a VM

Via console OCI:

1. **Compute → Instances → Create Instance**
2. **Image**: Canonical Ubuntu 22.04 (aarch64)
3. **Shape**: `VM.Standard.A1.Flex` — 2 OCPUs, 12 GB RAM
4. **Networking**: VCN com subnet pública e IP público
5. **SSH**: subir sua chave pública

### 2. Configurar Firewall

Na **Security List** da subnet, adicionar Ingress Rules:

| Source | Protocol | Port | Descrição |
|---|---|---|---|
| `0.0.0.0/0` | TCP | 80 | HTTP (redirect→HTTPS) |
| `0.0.0.0/0` | TCP | 443 | HTTPS |
| `<seu-ip>/32` | TCP | 22 | SSH (restrito) |

**⚠️ Atenção:** o Ubuntu na OCI vem com `iptables` bloqueando. Libere também no host:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

### 3. Bootstrap do Host

```bash
ssh ubuntu@<ip-público>

# Docker Engine + Compose v2 (ARM64)
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=arm64 signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu jammy stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
                    docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker $USER
newgrp docker
```

### 4. Deploy da Aplicação

```bash
git clone --recurse-submodules https://github.com/c4rlosfb/simples-editor.git
cd simples-editor
cp .env.example .env
nano .env   # Preencher SUPABASE_*, ajustar EXEC_TIMEOUT_S=15 (ARM)

docker compose up --build -d
docker compose ps
curl -k https://localhost/api/health
```

### 5. TLS com Let's Encrypt

```bash
# Apontar DNS tipo A: simples.seu-dominio.edu.br → <IP público>
# Depois:

sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

docker compose stop nginx

sudo certbot certonly --standalone -d simples.seu-dominio.edu.br \
     --non-interactive --agree-tos -m admin@seu-dominio.edu.br

sudo cp /etc/letsencrypt/live/simples.seu-dominio.edu.br/fullchain.pem \
       ./nginx/certs/
sudo cp /etc/letsencrypt/live/simples.seu-dominio.edu.br/privkey.pem \
       ./nginx/certs/

docker compose start nginx

# Renovação automática (cron)
echo "0 3 * * * certbot renew --quiet --post-hook \
  'cd /home/ubuntu/simples-editor && docker compose restart nginx'" \
  | sudo crontab -
```

Para detalhes completos, consulte [`DOMAIN.md`](./DOMAIN.md) e a seção 14.7 do [`PRD`](./prd-simples-online.md).

---

## Segurança

O Simples Editor foi projetado com **defense in depth** — 9 camadas de isolamento por execução, além de timeouts em cascata e rate limiting.

### 9 Camadas de Isolamento do Sandbox

| # | Camada | Mecanismo |
|---|---|---|
| 1 | Container descartável | `docker run --rm` — destruído após cada execução |
| 2 | Isolamento de rede | `--network=none` — zero acesso à rede |
| 3 | Filesystem imutável | `--read-only` + `tmpfs:/tmp,size=8m` |
| 4 | Limite de memória | `--memory=128m --memory-swap=128m` |
| 5 | Limite de CPU | `--cpus=0.5` (cgroups v2) |
| 6 | Limite de processos | `--pids-limit=64` — bloqueia fork bomb |
| 7 | Usuário não-root | `--user=65534:65534` (nobody) |
| 8 | Sem capabilities | `--cap-drop=ALL` |
| 9 | Seccomp | Perfil padrão do Docker — bloqueia syscalls perigosas |

### Timeouts em Cascata

```
┌──────────────────────────────────────────────────────────┐
│ [1] Compile timeout    subprocess.run(timeout=15)         │
│ [2] Wall-clock         asyncio.wait_for(exec, timeout=10) │
│     → SIGTERM (1s) → SIGKILL                             │
│ [3] Hard limit Docker  --stop-timeout=12                  │
└──────────────────────────────────────────────────────────┘
```

### Threat Model

| Ameaça | Mitigação |
|---|---|
| Loop infinito | Wall-clock timeout (10s) |
| Fork bomb | `--pids-limit=64` |
| Consumo de memória | `--memory=128m` |
| Exfiltração de dados | `--network=none` |
| Escape do container | Não-root + `--cap-drop=ALL` + seccomp |
| Abuso de execuções | Rate limit: 30/min por usuário, 120/min por IP |
| JWT roubado | Expiração curta (1h, Supabase) + RLS (v2) |
| Code injection | `subprocess` com lista de args — nunca `shell=True` |

### Rate Limiting

- **30 execuções/minuto** por `user_id`
- **120 execuções/minuto** por IP
- Implementado via `flask-limiter`

### Input Validation

- Código fonte limitado a 64 KB
- UTF-8 válido, apenas caracteres imprimíveis ASCII/extended
- Stdin ≤ 4 KB por mensagem WebSocket

---

## Documentação

| Documento | Descrição |
|---|---|
| [`PRD (prd-simples-online.md)`](./prd-simples-online.md) | Product Requirements Document completo — 1630 linhas cobrindo arquitetura, API, segurança, UI, testes |
| [`SPRINTS.md`](./SPRINTS.md) | Planejamento de 6 sprints com entregáveis e Definition of Done |
| [`PROGRESS.md`](./PROGRESS.md) | Acompanhamento granular de tarefas (checklist por sprint) |
| [`RETROSPECTIVE.md`](./RETROSPECTIVE.md) | Retrospectiva da equipe — aprendizados e próximos desafios |
| [`DOMAIN.md`](./DOMAIN.md) | Guia de configuração de domínio próprio + TLS |
| [`PRESENTATION.md`](./PRESENTATION.md) | Slides Marp para apresentação final |

---

## Equipe

<p align="center">
  <b>Desenvolvido para a disciplina de Compiladores</b><br>
  <b>IFSULDEMINAS — Campus Poços de Caldas</b><br>
  <b>Engenharia de Computação — 2026/1</b>
</p>

<div align="center">

| Integrante | GitHub | Papel |
|---|---|---|
| **Carlos Barboa** | [@c4rlosfb](https://github.com/c4rlosfb) | Arquiteto, Backend, DevOps, Segurança |
| **Luan Dias** | [@LuanCasDias](https://github.com/LuanCasDias) | Frontend, UI/UX, Monaco Editor |
| **Kauan Simão** | [@KauaN-png](https://github.com/KauaN-png) | Infraestrutura, Docker, Oracle Cloud |

</div>

---

## Licença

Este projeto está licenciado sob a [MIT License](./LICENSE) — veja o arquivo para detalhes.

---

<p align="center">
  <i>Feito com ❤️ no sul de Minas Gerais</i><br>
  <sub>Poços de Caldas, 2026</sub>
</p>
