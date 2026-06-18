# Incident Response Playbook — Sandbox Escape / Security Event

> **Propósito**: Guia de resposta para incidentes de segurança no Simples Editor.
> Foco principal: escape de sandbox, abuso de execução, e comprometimento do backend.
> **Público-alvo**: Equipe de plataforma / administradores do sistema.
>
> **Última auditoria**: 2026-06-17 — Todas as 9 camadas de isolamento, 3 timeouts,
> e 8 ameaças do threat model verificadas e conformes.

---

## Índice

0. [Auditoria de Segurança do Sandbox](#0-auditoria-de-segurança-do-sandbox)
   - [0.1 9 Camadas de Isolamento](#01-9-camadas-de-isolamento)
   - [0.2 3 Camadas de Timeout (Defense in Depth)](#02-3-camadas-de-timeout-defense-in-depth)
   - [0.3 Threat Model](#03-threat-model)
   - [0.4 Checklist de Verificação](#04-checklist-de-verificação)
1. [Matriz de severidade](#1-matriz-de-severidade)
2. [Incidentes conhecidos e resposta](#2-incidentes-conhecidos-e-resposta)
   - [2.1 Loop infinito não interrompido](#21-loop-infinito-não-interrompido)
   - [2.2 Fork bomb ou esgotamento de PIDs](#22-fork-bomb-ou-esgotamento-de-pids)
   - [2.3 Exfiltração de dados via rede](#23-exfiltração-de-dados-via-rede)
   - [2.4 Escape do container Docker](#24-escape-do-container-docker)
   - [2.5 Abuso de execuções (rate limit bypass)](#25-abuso-de-execuções-rate-limit-bypass)
   - [2.6 JWT comprometido](#26-jwt-comprometido)
   - [2.7 Vazamento de container (container leak)](#27-vazamento-de-container-container-leak)
   - [2.8 Code injection no backend](#28-code-injection-no-backend)
3. [Procedimento geral de resposta](#3-procedimento-geral-de-resposta)
4. [Pós-incidente](#4-pós-incidente)
5. [Checklist de recovery](#5-checklist-de-recovery)
6. [Contatos](#6-contatos)

---

## 0. Auditoria de Segurança do Sandbox

> **Data da auditoria**: 2026-06-17
> **Escopo**: Verificação das 9 camadas de isolamento Docker, 3 camadas de timeout,
> threat model e checklist de segurança conforme PRD §11.2 e §11.6.
> **Arquivos auditados**:
> - `backend/app/execution.py` (PtyExecutionStrategy)
> - `backend/app/sandbox.py` (SandboxFactory)
> - `backend/app/config.py` (Config / timeout defaults)
> - `backend/app/limits.py` (Rate limiting)
> - `backend/app/compiler.py` (CompilerService — compile timeout)
> - `backend/app/validation.py` (Input validation)
> - `backend/app/ws_handler.py` (WebSocket handler)
> - `backend/sandbox_config.py` (TimeoutConfig dataclass)

### 0.1 9 Camadas de Isolamento

Cada camada foi verificada no código-fonte do `PtyExecutionStrategy.execute()`
(`backend/app/execution.py`, linhas 80–97) e na `SandboxFactory.create_container()`
(`backend/app/sandbox.py`, linhas 68–85).

| # | Camada | Parâmetro Docker | Valor | Arquivo (linha) | Status |
|---|--------|-----------------|-------|-----------------|--------|
| 1 | **Container descartável** | `container.remove(force=True)` | Remoção forçada no `finally` | `execution.py:206-210` | ✅ Equivalente a `--rm` |
| 2 | **Network isolation** | `network_mode` | `"none"` | `execution.py:84` | ✅ |
| 3 | **Filesystem read-only** | `read_only` | `True` | `execution.py:89` | ✅ |
| 3a | **tmpfs limitado** | `tmpfs` | `{"/tmp": "size=8m"}` | `execution.py:90` | ✅ |
| 4 | **Memory limit** | `mem_limit` | `"128m"` | `execution.py:85` | ✅ |
| 4a | **Memory swap limit** | `memswap_limit` | `"128m"` | `execution.py:86` | ✅ |
| 5 | **CPU quota** | `cpu_quota` | `50000` (0.5 CPU) | `execution.py:87` | ✅ |
| 6 | **PIDs limit** | `pids_limit` | `64` | `execution.py:88` | ✅ |
| 7 | **Usuário não-root** | `user` | `"65534:65534"` (nobody) | `execution.py:91` | ✅ |
| 8 | **Capabilities drop** | `cap_drop` | `["ALL"]` | `execution.py:92` | ✅ |
| 9 | **Seccomp profile** | (Docker default) | Perfil padrão do Docker | Implícito — não desabilitado | ✅ |

**Nota sobre camada 1**: O código não passa `auto_remove=True` (equivalente ao flag
`--rm` do CLI). Em vez disso, o container é removido explicitamente no bloco `finally`
com `container.remove(force=True)`. O efeito é o mesmo: containers não persistem após
a execução, mesmo em caso de erro ou timeout.

**Verificação adicional — SandboxFactory**: O `SandboxFactory.create_default_config()`
(`sandbox.py:60-62`) e `SandboxFactory.create_container()` (`sandbox.py:64-88`)
espelham exatamente os mesmos parâmetros de segurança, garantindo consistência
por toda a aplicação. O `SandboxConfig` dataclass (`sandbox.py:20-43`) define os
valores padrão (`network_mode="none"`, `mem_limit="128m"`, etc.) com defaults
idênticos aos usados no `PtyExecutionStrategy`.

### 0.2 3 Camadas de Timeout (Defense in Depth)

Conforme PRD §11.3 e `backend/sandbox_config.py`, as três camadas operam em
sequência para garantir que nenhuma execução ultrapasse os limites:

| # | Camada | Mecanismo | Valor | Arquivo (linha) | Status |
|---|--------|----------|-------|-----------------|--------|
| 1 | **Compile timeout** | `subprocess.run(timeout=)` | **15s** | `compiler.py:136,161,174` | ✅ |
| 2 | **Wall-clock timeout** | `asyncio.wait_for(timeout=)` | **10s** | `execution.py:163` | ✅ |
| 3 | **Docker hard stop** | `stop_timeout=` | **12s** | `execution.py:96` | ✅ |

**Detalhamento**:

**Camada 1 — Compile timeout (15s)**:
- Aplica-se a cada estágio individualmente: `simplesc`, `nasm`, `ld`
- Todos usam `subprocess.run(..., timeout=config.compile_timeout_s)` com lista de args
- `compiler.py:132-137` — `_run_simplesc()`: timeout na compilação SIMPLES→NASM
- `compiler.py:157-163` — `_run_nasm()`: timeout na montagem NASM→ELF32
- `compiler.py:170-176` — `_run_ld()`: timeout na linkagem ELF32→binário
- O `TimeoutExpired` é capturado em `compiler.py:97-104` e retornado como
  `CompileResult(success=False, error_message="Compilation timed out...")`

**Camada 2 — Wall-clock timeout (10s)**:
- Aplica-se ao tempo total de execução do binário no sandbox
- Implementado via `asyncio.wait_for()` em `execution.py:162-164`
- Timeout vem de `config.exec_timeout_s` (default: 10, env: `EXEC_TIMEOUT_S`)
- Ao expirar: SIGTERM → sleep(1) → SIGKILL (`execution.py:166-172`)
- O `SIGTERM_GRACE_S = 1` (definido em `sandbox_config.py:24`) é respeitado

**Camada 3 — Docker hard stop (12s)**:
- Rede de segurança: se as camadas 1 e 2 falharem, o Docker força SIGKILL
- `stop_timeout=12` em `execution.py:96`
- `DOCKER_STOP_TIMEOUT_S = 12` em `sandbox_config.py:21`
- Invariante validada: `exec_timeout_s + sigterm_grace_s < docker_stop_timeout_s`
  (10 + 1 = 11 < 12 ✅) — `sandbox_config.py:72-84`

**Validação de invariante**: A função `validate_timeouts()` em `sandbox_config.py:72-84`
garante que o soft timeout (10s) + grace period (1s) é estritamente menor que o
Docker hard stop (12s). Isso evita que o Docker mate o container com SIGKILL antes
que a aplicação tente o graceful shutdown com SIGTERM.

### 0.3 Threat Model

Cada ameaça identificada no PRD §11.6 foi verificada contra as mitigações
implementadas no código.

| # | Ameaça | Mitigação(ões) | Implementação | Status |
|---|--------|---------------|---------------|--------|
| 1 | **Loop infinito** | Wall-clock timeout 10s + Docker stop_timeout 12s | `execution.py:162-172` (asyncio.wait_for + SIGTERM/SIGKILL) | ✅ |
| 2 | **Fork bomb** | `pids_limit=64` | `execution.py:88` | ✅ |
| 3 | **Memória ilimitada** | `mem_limit=128m` + `memswap_limit=128m` | `execution.py:85-86` | ✅ |
| 4 | **Exfiltração via rede** | `network_mode="none"` | `execution.py:84` | ✅ |
| 5 | **Escape do container** | user=65534:65534 + cap_drop=ALL + seccomp default + read_only fs | `execution.py:89,91,92` | ✅ |
| 6 | **Abuso de execuções** | Rate limit 30/min (user) + 120/min (IP) | `limits.py:33-44` (Flask-Limiter) | ✅ |
| 7 | **JWT roubado** | Expiração curta (Supabase padrão 1h) + validação `sub`/`exp` | `ws_handler.py:172-173` (verify_jwt + extract_user_id) | ✅ |
| 8 | **Code injection** | `subprocess.run` com lista de args, nunca `shell=True` | `compiler.py:132-136,157-162,170-175` | ✅ |

**Mitigações adicionais verificadas**:

| Medida | Descrição | Local |
|--------|----------|-------|
| Validação de entrada | Código limitado a 64 KB, apenas caracteres imprimíveis + ASCII estendido | `validation.py:19-52` |
| Validação de stdin | Dados stdin limitados a 4096 bytes | `validation.py:54-68` |
| Rate limit duplo | Limiter por user_id + limiter separado por IP | `limits.py:33-44` |
| Container cleanup | `container.remove(force=True)` no finally, mesmo em exceções | `execution.py:206-210` |
| Workdir cleanup | `shutil.rmtree()` no cleanup da conexão | `compiler.py:180-185` |
| Auth obrigatória | JWT verificado em todo WebSocket connect | `ws_handler.py:153-174` |

### 0.4 Checklist de Verificação

Itens verificados nesta auditoria (2026-06-17):

- [x] **Isolamento**: Todos os 9 parâmetros de segurança do Docker conferidos no `PtyExecutionStrategy.execute()`
- [x] **Isolamento**: `SandboxFactory` espelha os mesmos parâmetros (consistência via Factory pattern)
- [x] **Timeout 1**: `subprocess.run(timeout=15)` em todos os 3 estágios de compilação (simplesc, nasm, ld)
- [x] **Timeout 2**: `asyncio.wait_for(timeout=10)` no executor com sequência SIGTERM → SIGKILL
- [x] **Timeout 3**: `stop_timeout=12` no container Docker
- [x] **Invariante**: `exec_timeout_s + sigterm_grace_s < docker_stop_timeout_s` (11 < 12 ✅)
- [x] **Network**: `network_mode="none"` — sem interface de rede no container
- [x] **Filesystem**: `read_only=True` + `tmpfs` limitado a 8 MB
- [x] **Usuário**: `nobody:nobody` (UID 65534, GID 65534)
- [x] **Capabilities**: `cap_drop=["ALL"]` — todas as capabilities Linux removidas
- [x] **Seccomp**: Perfil padrão do Docker ativo (não desabilitado no código)
- [x] **Rate limit**: Flask-Limiter configurado para 30 req/min (user) + 120 req/min (IP)
- [x] **Code injection**: Nenhuma ocorrência de `shell=True` — todas as chamadas usam lista de args
- [x] **Validação**: Código validado (tamanho + charset) antes da compilação
- [x] **Validação**: Stdin validado (tamanho) antes do envio ao container
- [x] **JWT**: Autenticação obrigatória no WebSocket, verificação de `sub` e `exp`
- [x] **Cleanup**: Container removido no `finally`, workdir limpo na desconexão
- [x] **Docker client**: Inicialização lazy (`docker.from_env()`) — não cria conexão até necessário

### 0.5 Recomendações (não bloqueantes)

As seguintes medidas aumentariam a segurança mas não são requeridas para v1:

1. **`--security-opt=no-new-privileges`**: Impedir que processos no container
   adquiram novos privilégios via setuid/setgid. Não implementado atualmente.
2. **`--security-opt=seccomp=<profile.json>`**: Perfil seccomp customizado mais
   restritivo que o default do Docker (ex: bloquear `ptrace`, `mount`).
3. **`auto_remove=True`**: Usar remoção automática do Docker em vez de remoção
   manual no `finally` — mais idiomático e reduz chance de leak se o processo
   Python for morto antes do `finally`.
4. **gVisor / Firecracker**: Para isolamento mais forte (v2), considerar runtime
   com kernel em userspace (`runsc`) ou micro-VM (`firecracker-containerd`).
5. **Rate limit no Nginx**: Adicionar camada de rate limiting no reverse proxy
   (pré-backend) para proteção adicional contra DDoS.
6. **Monitoramento**: Adicionar métrica `simples_active_sandboxes` com alerta se
   > 50 containers simultâneos.

---

## 1. Matriz de severidade

| Severidade | Cor | Definição | SLA de resposta |
|------------|-----|-----------|-----------------|
| **Crítico** | 🔴 | Escape de sandbox confirmado ou comprometimento do host | Imediato (≤ 15 min) |
| **Alto** | 🟠 | Abuso de recursos que afeta múltiplos usuários | ≤ 1 hora |
| **Médio** | 🟡 | Violação de rate limit, container leak isolado | ≤ 4 horas |
| **Baixo** | 🟢 | Alarme falso, tentativa bloqueada sem dano | ≤ 24 horas |

---

## 2. Incidentes conhecidos e resposta

### 2.1 Loop infinito não interrompido

**Sintomas**:
- Container continua rodando após 15s do timeout configurado
- CPU elevada no host por processo do sandbox
- Reclamação de usuário sobre execução "travada"

**Camadas de defesa esperadas**:
1. `asyncio.wait_for` com timeout de 10s (wall-clock)
2. SIGTERM → 1s → SIGKILL
3. `--stop-timeout=12` no container Docker

**Resposta**:

| Passo | Ação | Responsável |
|-------|------|-------------|
| 1 | Verificar containers ativos: `docker ps --filter name=sim-*` | Plantonista |
| 2 | Identificar container pelo timestamp: `docker inspect <id> \| jq '.[].Created'` | Plantonista |
| 3 | Matar manualmente: `docker kill --signal=SIGKILL <id>` | Plantonista |
| 4 | Remover: `docker rm -f <id>` | Plantonista |
| 5 | Verificar logs do backend: `docker logs backend --since 5m` | Plantonista |
| 6 | Se recorrente, escalar para investigação do timeout handler | Dev lead |

**Mitigação permanente**:
- Ajustar `EXEC_TIMEOUT_S` para 8s (mais conservador)
- Adicionar alerta em `simples_active_sandboxes` > 50

---

### 2.2 Fork bomb ou esgotamento de PIDs

**Sintomas**:
- Container atinge `pids_limit=64` e é OOM-killed pelo cgroup
- Log: `docker: ResourceExhaustedError: pids limit`
- Host com carga alta repentina

**Camadas de defesa esperadas**:
1. `--pids-limit=64` no container
2. Cgroups do Docker limitam forks

**Resposta**:

| Passo | Ação | Responsável |
|-------|------|-------------|
| 1 | Verificar se o container foi automaticamente morto pelo Docker | Plantonista |
| 2 | Confirmar pelo log: `docker logs backend \| grep "pids limit"` | Plantonista |
| 3 | Se container ainda ativo: `docker kill <id>` | Plantonista |
| 4 | Verificar se há múltiplos containers do mesmo usuário (abuso) | Plantonista |
| 5 | Identificar user_id nos logs e bloquear temporariamente via rate limit | Plantonista |

**Mitigação permanente**:
- Reduzir `pids_limit` para 32 se falso positivo for aceitável
- Implementar auditoria de código suspeito (regex por `fork`)

---

### 2.3 Exfiltração de dados via rede

**Sintomas**:
- Tráfego de saída detectado do container sandbox (impossível por design)
- Tentativa de conexão bloqueada (logs do Docker)

**Camadas de defesa esperadas**:
1. `--network=none` — container sem interface de rede

**Resposta**:

| Passo | Ação | Responsável |
|-------|------|-------------|
| 1 | Confirmar que `--network=none` está presente: `docker inspect <id> \| jq '.[].HostConfig.NetworkMode'` | Plantonista |
| 2 | Se network_mode não for "none", incidente crítico — container foi modificado | Plantonista |
| 3 | Verificar logs do daemon Docker: `journalctl -u docker --since 5m` | Dev lead |
| 4 | Isolar o host da rede se necessário: `iptables -A INPUT -s <ip> -j DROP` | Dev lead |
| 5 | Escalar para segurança da instituição | Coordenador |

**Mitigação permanente**:
- Validar `network_mode` em código (teste unitário no `SandboxFactory`)
- Adicionar monitoramento de tráfego de saída nos hosts Docker

---

### 2.4 Escape do container Docker

**Sintomas**:
- Arquivos criados fora do container no host
- Processos do host sendo manipulados a partir do sandbox
- Usuário `nobody` (UID 65534) aparece em operações fora do esperado

**Camadas de defesa esperadas**:
1. `--user=65534:65534` (nobody)
2. `--cap-drop=ALL`
3. Seccomp profile padrão do Docker
4. `--read-only` (filesystem imutável)
5. Sem montagem do socket Docker

**Resposta**:

| Passo | Ação | Responsável |
|-------|------|-------------|
| **CRÍTICO** | Isolar o host imediatamente: remover da rota do Nginx | Plantonista |
| 2 | Parar o backend: `docker compose stop backend` | Plantonista |
| 3 | Coletar evidências: `docker inspect <id> > /tmp/escape-$(date +%s).json` | Plantonista |
| 4 | Salvar logs: `docker logs backend > /tmp/backend-$(date +%s).log` | Plantonista |
| 5 | Salvar syslog: `journalctl -u docker --since 1h > /tmp/docker-$(date +%s).log` | Plantonista |
| 6 | Verificar se o host foi comprometido: `rkhunter --check` ou `chkrootkit` | Dev lead |
| 7 | Rotacionar todas as chaves e segredos do ambiente (Supabase JWT, etc.) | Coordenador |
| 8 | Notificar a equipe de segurança da instituição e a coordenação do curso | Coordenador |

**Mitigação permanente**:
- Adicionar `--security-opt=no-new-privileges`
- Considerar `gVisor` ou `Firecracker` para isolamento mais forte (v2)
- Auditoria mensal das flags de segurança do Docker

---

### 2.5 Abuso de execuções (rate limit bypass)

**Sintomas**:
- Mais de 30 execuções/minuto de um mesmo `user_id`
- Mais de 120 execuções/minuto de um mesmo IP
- Backend com latência alta, fila de execução crescente

**Camadas de defesa esperadas**:
1. Rate limit por `user_id`: 30 exec/min (`flask-limiter`)
2. Rate limit por IP: 120 exec/min

**Resposta**:

| Passo | Ação | Responsável |
|-------|------|-------------|
| 1 | Identificar user_id ou IP abusivo nos logs | Plantonista |
| 2 | Bloquear manualmente: adicionar à blacklist no Redis ou config | Plantonista |
| 3 | Verificar se é um aluno legítimo com script automatizado | Plantonista |
| 4 | Notificar o usuário (se identificado) sobre uso aceitável | Plantonista |
| 5 | Se for ataque automatizado, manter bloqueio e escalar | Dev lead |

**Mitigação permanente**:
- Implementar rate limit no Nginx (pré-backend) para proteção adicional
- Adicionar captcha para execuções frequentes (opcional)
- Logging de rate limit hits para análise

---

### 2.6 JWT comprometido

**Sintomas**:
- Requests com JWT válido de um IP inesperado
- Múltiplos user_ids diferentes do mesmo IP
- Acesso a recursos de outro usuário (impossível em v1, mas monitorar)

**Camadas de defesa esperadas**:
1. JWT expira em 1h (padrão Supabase)
2. Backend valida `sub` e `exp` em toda requisição

**Resposta**:

| Passo | Ação | Responsável |
|-------|------|-------------|
| 1 | Identificar o usuário afetado pelo `sub` do JWT | Plantonista |
| 2 | Invalidar sessões no Supabase (revogar tokens do usuário) | Plantonista |
| 3 | Solicitar que o usuário troque a senha | Plantonista |
| 4 | Verificar logs de acesso do usuário para atividades suspeitas | Dev lead |
| 5 | Se for JWT de serviço (anon key), rotacionar imediatamente | Coordenador |

**Mitigação permanente**:
- Implementar RLS (Row-Level Security) nas tabelas futuras (v2)
- Logging de user_id em todas as operações

---

### 2.7 Vazamento de container (container leak)

**Sintomas**:
- `docker ps` mostra containers parados ou em execução por horas
- Uso de disco crescente (camadas de container não removidas)
- Número de containers excede o esperado (deveria ser ~0 em idle)

**Camadas de defesa esperadas**:
1. `container.remove(force=True)` no finally do executor
2. Cron de limpeza diário

**Resposta**:

| Passo | Ação | Responsável |
|-------|------|-------------|
| 1 | Listar containers órfãos: `docker ps -a --filter name=sim-* --format '{{.ID}} {{.CreatedAt}}'` | Plantonista |
| 2 | Remover todos os containers órfãos: `docker rm -f $(docker ps -a -q --filter name=sim-*)` | Plantonista |
| 3 | Verificar logs do backend para identificar a causa do leak | Dev lead |
| 4 | Se aplicável, corrigir o handler de exceção que pulou o `finally` | Dev lead |

**Mitigação permanente**:
- Cron job: `0 3 * * * docker container prune --filter label=simples-sandbox --force`
- Métrica `simples_active_sandboxes` com alerta se > threshold por > 5 min

---

### 2.8 Code injection no backend

**Sintomas**:
- Comandos arbitrários executados no host backend
- Logs com comandos inesperados
- Arquivos modificados no backend

**Camadas de defesa esperadas**:
1. Backend usa `subprocess.run` com lista de args (nunca `shell=True`)
2. Validação de código (tamanho, caracteres, UTF-8)

**Resposta**:

| Passo | Ação | Responsável |
|-------|------|-------------|
| **CRÍTICO** | Parar o backend: `docker compose stop backend` | Plantonista |
| 2 | Isolar o host da rede | Plantonista |
| 3 | Coletar logs completos do backend | Dev lead |
| 4 | Identificar o código malicioso que causou a injeção | Dev lead |
| 5 | Corrigir a vulnerabilidade e fazer deploy | Dev lead |
| 6 | Auditoria completa do host (rootkits, backdoors) | Coordenador |

**Mitigação permanente**:
- Sempre usar lista de args em `subprocess.run`
- Adicionar `shell=True` detector em code review
- Testes de fuzzing no validador de entrada

---

## 3. Procedimento geral de resposta

### 3.1 Triage (primeiros 5 minutos)

```mermaid
flowchart TD
    A[Alarme/Report] --> B{Container ativo?}
    B -->|Sim| C[Identificar container]
    B -->|Não| D[Verificar logs]
    C --> E{Network=none?}
    E -->|Sim| F[Verificar pids/mem]
    E -->|Não| G[INCIDENTE CRÍTICO]
    F --> H{Dentro dos limites?}
    H -->|Sim| I[Monitorar]
    H -->|Não| J[Kill container]
    D --> K[Analisar causa raiz]
```

### 3.2 Comunicação

| Canal | Quando usar |
|-------|-------------|
| Notificação automática (cron/alertmanager) | Alarme de métrica (`simples_active_sandboxes`, `simples_executions_total`) |
| Grupo da equipe (WhatsApp/Telegram) | Incidente de severidade Alta ou Crítica |
| Email institucional | Pós-incidente (relatório completo) |
| Sala de aula / Professor | Se um aluno específico estiver envolvido |

### 3.3 Escalação

```
Plantonista (N1) ── não resolve em 15min? ──> Dev lead (N2) ──> Coordenador (N3)
```

- **N1 (Plantonista)**: Estudante da equipe em rodízio semanal
- **N2 (Dev lead)**: Carlos Barbosa (carlos.barbosa@ifsuldeminas.edu.br)
- **N3 (Coordenador)**: Professor responsável pela disciplina

---

## 4. Pós-incidente

Após resolução de qualquer incidente de severidade **Alta** ou **Crítica**:

1. **Reunião post-mortem** em até 48h
2. **Documentar** no final deste arquivo (seção 4.1)
3. **Atualizar** as camadas de defesa se aplicável
4. **Testar** a correção com cenário reproduzível
5. **Compartilhar** lições aprendidas com a equipe

### 4.1 Registro de incidentes

| Data | Severidade | Tipo | Resumo | Responsável | Ações tomadas |
|------|------------|------|--------|-------------|---------------|
| — | — | — | — | — | — |

---

## 5. Checklist de recovery

Após um incidente crítico, seguir esta ordem:

- [ ] Host isolado da rede (se aplicável)
- [ ] Backend parado
- [ ] Evidências coletadas (logs, inspect, syslog)
- [ ] Container malicioso removido
- [ ] Host verificado (rootkits, backdoors)
- [ ] Segredos rotacionados (JWT secret, Supabase keys)
- [ ] Código corrigido e revisado
- [ ] Deploy da correção em staging
- [ ] Testes de segurança executados
- [ ] Deploy em produção
- [ ] Post-mortem realizado
- [ ] Documentação atualizada

---

## 6. Contatos

| Papel | Nome | Email | Telefone |
|-------|------|-------|----------|
| Dev lead | Carlos Barbosa | carlos.barbosa@ifsuldeminas.edu.br | — |
| Professor | — | — | — |
| Administrador Supabase | — | — | — |
| Administrador OCI | — | — | — |
| Segurança institucional | — | — | — |
