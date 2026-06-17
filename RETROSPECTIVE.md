# Retrospectiva da Equipe — Simples Editor

> Disciplina de Compiladores — IFSULDEMINAS Campus Poços de Caldas  
> Engenharia de Computação, 2026/1  
> **Integrantes:** Carlos Barboa, Luan Dias, Kauan Simão

---

## 1. Visão Geral do Projeto

O **Simples Editor** é uma Web IDE para a linguagem didática SIMPLES (27 palavras reservadas em português estruturado), permitindo que alunos escrevam, compilem e executem código diretamente no navegador — com visualização lado-a-lado do assembly NASM x86 32-bit gerado e terminal interativo via xterm.js.

Ao final do semestre, entregamos:

| Entregável | Status |
|---|---|
| **45/47 issues concluídas** | ✅ |
| **30+ PRs mergeados** | ✅ |
| **110+ testes passando** | ✅ |
| **Docker Compose funcional** (3 containers) | ✅ |
| **Monaco Editor** com 27 keywords SIMPLES | ✅ |
| **API REST** (`/api/health`, `/api/compile`, `/api/auth/verify`, `/api/limits`) | ✅ |
| **WebSocket `/ws/run`** com máquina de estados | ✅ |
| **Pipeline de compilação** (simplesc → nasm → ld) com mock fallback | ✅ |
| **9 camadas de isolamento** por sandbox Docker | ✅ |
| **Supabase Auth** configurado com JWT real | ✅ |
| **GitHub Actions CI** | ✅ |
| **Documentação** (~3000 linhas: PRD, README, SPRINTS, guias, apresentação) | ✅ |
| **Deploy Oracle Cloud** (IaC pronta) | ⚠️ Pendente credenciais |
| **Domínio próprio com TLS** | ⚠️ Pendente #48 |

---

## 2. Fase de Planejamento — O que Aprendemos

### 2.1 PRD como contrato de time
A decisão de escrever um PRD de 1630 linhas antes de qualquer código foi acertada. Cobrir user stories, arquitetura detalhada, threat model, API design e Definition of Done de cada sprint nos deu um norte claro. **Documentação não é burocracia — é alinhamento.**

### 2.2 Kanban e GitHub Projects
Configurar o quadro com colunas Backlog → In Progress → In Review → Done e automações via GitHub Actions nos ensinou na prática como rastrear trabalho em equipe. Subestimamos a disciplina necessária para manter o quadro atualizado — vários itens ficaram desatualizados e o agente Hermes precisou corrigir o Kanban múltiplas vezes.

### 2.3 Infraestrutura como Código (IaC)
Os scripts Terraform para Oracle Cloud Ampere A1 (Always Free) foram um aprendizado concreto de provisionamento declarativo. Porém, sem credenciais OCI, o `terraform apply` nunca foi executado — a IaC está pronta mas o deploy real é a única pendência.

### 2.4 Uso de agentes autônomos (Hermes)
O uso do agente Hermes como orquestrador — criando subagentes para revisão de PRs, correção de bugs, implementação de issues e gerenciamento do Kanban — foi o diferencial técnico do projeto. Criamos PRDs específicos para agentes (`PRD-AGENTES.md`, `PRD-ISSUES.md`) e um fluxo de trabalho onde cada integrante delegava tarefas ao seu agente. Isso acelerou a fase final em ~10x.

---

## 3. O que Deu Certo

### 3.1 Pipeline de compilação com fallback mock
`POST /api/compile` com timeouts de 15s por estágio e fallback para mock quando `simplesc` não está disponível. Funciona tanto em produção (compilação real) quanto em desenvolvimento/demo (NASM mockado).

### 3.2 Docker Compose funcional
Após várias tentativas, conseguimos um `docker compose up` que sobe 3 containers (nginx, frontend, backend) em menos de 30 segundos. O backend responde em `/api/health` com status de todos os componentes.

### 3.3 Sandbox com 9 camadas de isolamento
`--network=none`, `--read-only`, `--cap-drop=ALL`, `--pids-limit=64`, `--memory=128m`, `--cpus=0.5` e timeouts em cascata. Auditamos fork bombs, tentativas de escrita e acesso à rede — tudo bloqueado.

### 3.4 Tokenizer Monarch + tema dark
Registrar a linguagem SIMPLES no Monaco Editor com 27 keywords coloridas (ciano, laranja, verde) deu credibilidade imediata ao projeto visualmente.

### 3.5 Integração Supabase
Credenciais reais configuradas, JWT validation no backend, `@supabase/auth-ui-react` no frontend, modo demo para apresentações sem login.

### 3.6 Colaboração agente-humano
A parceria com o Hermes permitiu que Carlos concentrasse esforço em decisões de arquitetura enquanto o agente executava tarefas repetitivas (revisão de PRs, correção de bugs, atualização de Kanban, merge de PRs). O resultado foi 45 issues fechadas em ~4 dias de trabalho intensivo.

---

## 4. O que Não Funcionou / Dificuldades

### 4.1 Conflitos de merge em massa
30+ branches criadas por 3 pessoas + 2 agentes geraram conflitos frequentes nos arquivos compartilhados (docker-compose, package.json, requirements.txt). A falta de um PR bootstrap único para o frontend fez cada PR carregar o scaffold inteiro.

### 4.2 `__pycache__/` versionado
Múltiplos PRs commitavam arquivos `.pyc` — foram necessárias várias limpezas manuais e reforço do `.gitignore` para resolver.

### 4.3 Docker no Windows
O `apt-get` dentro de containers Ubuntu falhou no Docker Desktop Windows por restrições de rede. Tivemos que criar um `Dockerfile.demo` alternativo baseado em `python:3.11-slim` para viabilizar a demonstração.

### 4.4 Duplicação de módulos Python
Conflito `backend/app.py` vs `backend/app/__init__.py` quebrou imports. Módulos duplicados entre `backend/` e `backend/app/` (compiler, auth, config, ws_handler) existiam em dois lugares. Resolvido com limpeza pós-merge.

### 4.5 Desbalanceamento de carga
Carlos concentrou a maior parte das implementações e orquestração. Luan contribuiu com documentação e infraestrutura. Kauan implementou várias features mas precisou de correções em keywords SIMPLES e stack. O uso de agentes autônomos ajudou a compensar, mas a distribuição humana foi desigual.

### 4.6 Itens não concluídos
- **Deploy Oracle Cloud** (#48): IaC pronta, VM nunca provisionada (sem credenciais OCI)
- **Domínio próprio com TLS** (#49): Bloqueado pelo #48
- **Compilação real**: Funciona se `simplesc` estiver no PATH; na demo usa mock
- **Supabase health**: Endpoint mostra "degraded" por detalhe de implementação (cosmético)

---

## 5. O que Faríamos Diferente

1. **MVP vertical na semana 2**: login → editor → compilar → ver NASM, iterando documentação junto
2. **1 PR bootstrap de frontend**: evitar que 10 PRs diferentes recriassem o mesmo scaffold
3. **Daily standups de 10 min**: teriam identificado desbalanceamento e bloqueios antes
4. **Deploy contínuo desde o Sprint 2**: testar em staging, não só local
5. **Testes desde o Sprint 1**: começamos tarde (Sprint 5-6)
6. **Agentes desde o início**: o uso de agentes na fase final foi revolucionário; ter começado antes teria evitado acúmulo

---

## 6. Contribuições

| Integrante | Principais entregas |
|---|---|
| **Carlos Barboa** | Arquitetura, PRD, backend completo, DevOps, segurança, documentação, orquestração de agentes, revisão de PRs |
| **Luan Dias** | Documentação (INCIDENTS.md), scripts de infraestrutura, testes de cobertura |
| **Kauan Simão** | Docker, empacotamento simplesc, frontend (health, tema, NASM panel, 3-painéis), testes E2E Playwright, correções de bugs |

---

## 7. Conclusão

O **Simples Editor** foi um projeto ambicioso para uma disciplina de um semestre. Entregamos um protótipo funcional com pipeline completo — editar código SIMPLES no navegador, compilar, ver assembly e executar em sandbox seguro — usando stack real de indústria (React + Flask + Docker + WebSocket + Supabase).

O uso de agentes autônomos (Hermes) como acelerador de desenvolvimento foi o diferencial que permitiu fechar 45 issues em tempo recorde. Aprendemos que **delegar tarefas mecânicas a agentes libera o engenheiro para pensar em arquitetura e tomar decisões**.

Falhamos na distribuição de carga humana e na comunicação síncrona. Mas os aprendizados — técnicos e de equipe — superam as falhas. Se recomeçássemos hoje, faríamos mob programming nas semanas 1-2, deploy contínuo desde o Sprint 2, e usaríamos agentes desde o primeiro dia.

---

*Poços de Caldas, junho de 2026.*
