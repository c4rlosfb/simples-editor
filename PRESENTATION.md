---
marp: true
theme: default
class: lead
footer: "IFSULDEMINAS — Campus Poços de Caldas | Compiladores 2026/1"
paginate: true
---

# Simples Editor

## Web IDE para a Linguagem SIMPLES

**Engenharia de Computação — Compiladores**

Carlos Barboa · Luan Dias · Kauan Simão

Junho 2026

---

## Agenda

1. O Problema
2. Nossa Solução
3. Arquitetura
4. Stack Tecnológica
5. Funcionalidades Implementadas
6. Demonstração ao Vivo
7. Segurança (Defense in Depth)
8. Resultados (Testes, Issues)
9. Lições Aprendidas
10. Conclusão

---

## O Problema

<div style="font-size: 0.9em;">

- ⚙️ **Instalação complexa de toolchain** (NASM, ld, binutils i686) para alunos iniciantes
- 🔓 **Execução insegura** de código arbitrário em laboratórios compartilhados
- 📉 **Falta de feedback visual** — alunos não veem relação entre código fonte e assembly gerado
- 🖥️ **Ambiente heterogêneo** — Windows, macOS, Linux com diferentes configurações
- ⏳ **Tempo perdido** em setup ao invés de aprendizado de compiladores

</div>

---

## Nossa Solução

<div style="font-size: 0.85em;">

### Simples Editor — IDE Web Completa

| Antes | Depois |
|---|---|
| Instalar NASM, ld, binutils | **Zero instalação** — abre o navegador |
| Executar binários localmente (risco) | **Sandbox Docker descartável** com 9 camadas de isolamento |
| Código fonte + assembly em arquivos separados | **Visualização lado-a-lado** com Monaco Editor |
| Terminal separado para I/O | **Terminal integrado** via xterm.js + WebSocket |
| `leia`/`escreva` não testáveis em batch | **Interatividade real** stdin/stdout via PTY |

</div>

---

## Arquitetura

```
┌──────────────────────────────────────────────────────────────────┐
│                       🌐 Navegador do Aluno                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │  Monaco Editor   │  │  NASM Viewer     │  │  xterm.js     │  │
│  │  (SIMPLES)       │  │  (asm x86 32)    │  │  (Terminal)   │  │
│  └────────┬─────────┘  └────────▲─────────┘  └───────┬───────┘  │
│           │     HTTPS/REST      │              WSS    │          │
└───────────┼─────────────────────┼─────────────────────┼──────────┘
            │                     │                     │
     ┌──────▼─────────────────────▼─────────────────────▼──────────┐
     │                      🔀 Nginx (Reverse Proxy)                │
     │                    TLS termination + WebSocket upgrade       │
     └──────┬──────────────────────┬──────────────────────┬────────┘
            │                      │                      │
     ┌──────▼──────┐       ┌───────▼────────┐     ┌──────▼─────────┐
     │  Frontend   │       │    Backend      │     │   Supabase     │
     │  React 18   │       │  Flask 3.x      │     │   (Auth JWT)   │
     │  TanStack   │       │  flask-sock     │     │   Cloud Free   │
     │  Nginx:alp  │       │  docker-py      │     └────────────────┘
     └─────────────┘       │  simplesc       │
                           │  nasm + ld      │
                           │  structlog      │
                           └───────┬─────────┘
                                   │ docker run --rm
                                   │ --network=none
                                   │ --read-only
                                   │ --cap-drop=ALL
                           ┌───────▼─────────┐
                           │  🐳 Sandbox      │
                           │  simples-runner  │
                           │  qemu-i386       │
                           │  (ELF i386)      │
                           └─────────────────┘
```

---

## Stack Tecnológica

<div style="font-size: 0.8em;">

### Frontend
| Tecnologia | Versão | Função |
|---|---|---|
| React | 18.x | UI Framework |
| TypeScript | 5.x | Tipagem estática |
| TanStack Start | latest | Full-stack React |
| Monaco Editor | latest | Editor de código (núcleo VS Code) |
| xterm.js | 5.x | Terminal interativo |
| Tailwind CSS | 3.x | Estilização |
| react-resizable-panels | latest | Splitters arrastáveis |
| @supabase/supabase-js | 2.x | Cliente Auth |

### Backend
| Tecnologia | Função |
|---|---|
| Python 3.11+ | Linguagem |
| Flask 3.x | API REST |
| flask-sock | WebSocket |
| docker SDK 7.x | Spawn de sandboxes |
| structlog | Logs JSON |
| prometheus-client | Métricas |
| flask-limiter | Rate limiting |
| pytest 8.x | Testes |

</div>

---

## Pipeline de Compilação

```
┌──────────────────────────────────────────────────────────────┐
│                    Pipeline de Compilação                     │
│                                                              │
│  Código SIMPLES                                              │
│       │                                                      │
│       ▼                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐               │
│  │ simplesc │───▶│   NASM   │───▶│    ld    │               │
│  │  (C99)   │    │ -f elf32 │    │-m elf_i38│               │
│  │  15s     │    │   15s    │    │   15s    │               │
│  └──────────┘    └──────────┘    └──────────┘               │
│       │               │               │                      │
│       ▼               ▼               ▼                      │
│   .asm (NASM)     .o (OBJ)      ELF i386                     │
│                                                              │
│       ┌──────────────────────────────────────┐               │
│       │  🎭 Mock Fallback                    │               │
│       │  Se simplesc não disponível:         │               │
│       │  gera NASM didático estruturado      │               │
│       └──────────────────────────────────────┘               │
│                                                              │
│                          ELF i386                             │
│                             │                                │
│                             ▼                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  🐳 Sandbox Docker (descartável)                     │    │
│  │  qemu-i386-static /sandbox/prog                      │    │
│  │  --network=none --read-only --cap-drop=ALL            │    │
│  │  --memory=128m --cpus=0.5 --pids-limit=64             │    │
│  │                                │                      │    │
│  │              ┌─────────────────┴──────────────┐       │    │
│  │              ▼                                 ▼       │    │
│  │         stdout/stderr                      stdin       │    │
│  │              │                                 │       │    │
│  └──────────────┼─────────────────────────────────┼───────┘    │
│                 │          WebSocket              │            │
│                 └──────────┬──────────────────────┘            │
│                            ▼                                   │
│                     🖥️  xterm.js                               │
│                     (Navegador)                                │
└──────────────────────────────────────────────────────────────┘
```

---

## Funcionalidades Implementadas

<div style="font-size: 0.78em;">

### ✅ Core (Sprints 1-2)
- 🔐 **Auth JWT** Supabase — login email/senha + modo demo
- ✏️ **Monaco Editor** — 27 keywords SIMPLES com syntax highlighting (ciano, laranja, verde)
- 📊 **Layout 3-painéis** — splitters arrastáveis com double-click collapse
- 📖 **4 exemplos built-in** — Hello World, Fatorial, Fibonacci, Tabuada

### ✅ Compilação (Sprint 3)
- ⚡ `POST /api/compile` — REST endpoint com timeout 15s
- 🔴 **Monaco markers** — erros destacados na linha/coluna exata
- 📝 **NASM viewer** — painel direito preenchido automaticamente
- 🎭 **Mock fallback** — NASM didático quando `simplesc` indisponível

### ✅ Execução Interativa (Sprint 4)
- 🔄 **WebSocket `/ws/run`** — máquina de estados IDLE→COMPILING→EXECUTING
- 🖥️ **xterm.js** — terminal real com `leia`/`escreva` interativo
- ⏹️ **Botão Stop** — SIGTERM → SIGKILL em cascata
- ⏱️ **Timeouts** — wall-clock 10s, hard limit Docker 12s

### ✅ Segurança & Observabilidade (Sprint 5)
- 🐳 **9 camadas de isolamento** — sem rede, read-only, sem capabilities
- 🚦 **Rate limiting** — 30/min por user, 120/min por IP
- 📊 **Prometheus metrics** — `/metrics` com histogramas
- 📝 **structlog JSON** — todos os logs estruturados

</div>

---

## Demonstração — Fluxo de Uso

<!-- _footer: "IFSULDEMINAS — Campus Poços de Caldas | Demo ao vivo" -->

<div style="font-size: 0.85em;">

1. **Acesso** → `http://localhost` → tela de login (ou modo demo)

2. **Editor** → Digitar código SIMPLES com highlighting:
   ```
   programa soma
     inteiro a, b, resultado
   inicio
     leia a
     leia b
     resultado := a + b
     escreva resultado
   fim
   ```

3. **▶ Compilar** → `POST /api/compile` → NASM aparece no painel direito

4. **▶ Executar** → WebSocket → container Docker sobe → terminal interativo:
   - Programa pergunta: `Digite o primeiro número:`
   - Usuário digita: `42`
   - Programa pergunta: `Digite o segundo número:`
   - Usuário digita: `17`
   - Saída: `59`
   - `[exit code: 0 — 1.42s]`

5. **■ Parar** → SIGTERM → container destruído em < 2s

6. **Erro** → Código inválido → marcadores vermelhos no editor

</div>

---

## Segurança — 9 Camadas de Isolamento

<div style="font-size: 0.75em;">

| # | Camada | Mecanismo | Ameaça Mitigada |
|---|---|---|---|
| 1 | Container descartável | `docker run --rm` | Persistência de malware |
| 2 | Isolamento de rede | `--network=none` | Exfiltração de dados |
| 3 | Filesystem imutável | `--read-only` + `tmpfs:/tmp,size=8m` | Escrita maliciosa |
| 4 | Limite de memória | `--memory=128m --memory-swap=128m` | Consumo de recursos |
| 5 | Limite de CPU | `--cpus=0.5` (cgroups v2) | CPU exhaustion |
| 6 | Limite de processos | `--pids-limit=64` | Fork bomb |
| 7 | Usuário não-root | `--user=65534:65534` (nobody) | Escalação de privilégio |
| 8 | Sem capabilities | `--cap-drop=ALL` | Syscalls privilegiadas |
| 9 | Seccomp | Perfil padrão Docker | Syscalls perigosas |

</div>

### Timeouts em Cascata

```
Compile timeout (15s) → Wall-clock (10s) → SIGTERM (1s) → SIGKILL → Hard limit Docker (12s)
```

---

## Resultados

<div style="font-size: 0.82em;">

| Métrica | Valor |
|---|---|
| **Issues concluídas** | 45/47 (96%) — #48 e #49 pendentes (Oracle Cloud) |
| **PRs mergeados** | 30+ |
| **Testes backend** | 110+ passando (pytest) |
| **Módulos testados** | 9 (auth, compiler, routes, ws_handler, sandbox, execution, validation, errors, config) |
| **Sprints concluídos** | 5/6 (Sprint 6 parcial) |
| **Cobertura do PRD** | ~90% funcionalidades implementadas |
| **Documentação** | ~3500 linhas (README, PRD, SPRINTS, guias, apresentação) |
| **Linhas de código** | ~8000 (frontend + backend + testes + infra) |

### Pendências

| Item | Status | Bloqueio |
|---|---|---|
| Deploy Oracle Cloud (#48) | ⚠️ IaC pronta | Credenciais OCI |
| Domínio próprio TLS (#49) | ⚠️ Bloqueado | Depende de #48 |
| Testes E2E Playwright | 🔄 Parcial | Em andamento |
| Cobertura ≥ 70% backend | 🔄 ~60% | Mais testes necessários |

</div>

---

## Lições Aprendidas

<div style="font-size: 0.8em;">

### ✅ O que deu certo

1. **PRD como contrato** — 1630 linhas antes do código = alinhamento total
2. **Docker Compose funcional** — 3 containers em < 30s de startup
3. **Sandbox com 9 camadas** — auditado: fork bomb, escrita, rede → tudo bloqueado
4. **Tokenizer Monarch** — 27 keywords coloridas deram credibilidade imediata
5. **Agentes autônomos (Hermes)** — 45 issues em ~4 dias, aceleração 10x

### ❌ O que faríamos diferente

1. **MVP vertical na semana 2** — login → editor → compilar → ver NASM
2. **1 PR bootstrap de frontend** — evitar 10 PRs recriando scaffold
3. **Deploy contínuo desde Sprint 2** — staging, não só local
4. **Testes desde Sprint 1** — começamos tarde (Sprint 5-6)
5. **Agentes desde o início** — uso revolucionário na fase final

### 📊 Distribuição

| Integrante | Foco |
|---|---|
| **Carlos Barboa** | Arquitetura, PRD, backend, DevOps, segurança, orquestração |
| **Luan Dias** | Documentação, infraestrutura, testes de cobertura |
| **Kauan Simão** | Docker, simplesc, frontend, testes E2E |

</div>

---

## Conclusão

<div style="font-size: 0.85em;">

### Entregamos ✓

- 🔧 **Web IDE funcional** para a linguagem SIMPLES
- 🐳 **Sandbox seguro** com 9 camadas de isolamento
- ⚡ **Pipeline completo** — editar → compilar → assembly → executar
- 🖥️ **Terminal interativo real** — `leia`/`escreva` extremo-a-extremo
- 📊 **Observabilidade** — métricas, logs JSON, health checks
- 📚 **Documentação abrangente** — PRD, README, guias, apresentação

### Diferencial Técnico

> Uso de **agentes autônomos (Hermes)** como acelerador de desenvolvimento:
> criação de subagentes para revisão de PRs, correção de bugs,
> implementação de issues e gerenciamento de Kanban.
> 
> _"Delegar tarefas mecânicas a agentes libera o engenheiro para pensar em arquitetura."_

</div>

---

<!-- _class: lead -->

# Obrigado!

## Simples Editor — Web IDE para a Linguagem SIMPLES

**https://github.com/c4rlosfb/simples-editor**

<div style="font-size: 0.8em; margin-top: 2em;">

Carlos Barboa — [@c4rlosfb](https://github.com/c4rlosfb)  
Luan Dias — [@LuanCasDias](https://github.com/LuanCasDias)  
Kauan Simão — [@KauaN-png](https://github.com/KauaN-png)

**IFSULDEMINAS — Campus Poços de Caldas**  
Engenharia de Computação — Compiladores 2026/1

</div>
