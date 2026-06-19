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
| **53/53 issues concluídas (100%)** | ✅ |
| **30+ PRs mergeados** | ✅ |
| **178 testes passando (79% cobertura)** | ✅ |
| **Docker Compose funcional** (3 containers) | ✅ |
| **Monaco Editor** com 27 keywords SIMPLES | ✅ |
| **API REST** (`/api/health`, `/api/compile`, `/api/limits`) | ✅ |
| **WebSocket `/ws/run`** com máquina de estados | ✅ |
| **Pipeline de compilação** (simplesc → nasm → ld) com mock fallback | ✅ |
| **9 camadas de isolamento** por sandbox Docker | ✅ |
| **Supabase Auth** com tela de login funcional | ✅ |
| **HTTPS via Let's Encrypt** (domínio nip.io) | ✅ |
| **Deploy Oracle Cloud** (VM Ampere A1) | ✅ |
| **Domínio público**: https://simples.163.176.220.47.nip.io | ✅ |
| **GitHub Actions CI** | ✅ |
| **Documentação** (~3500 linhas: PRD, README, SPRINTS, DOMAIN, INCIDENTS, apresentação) | ✅ |

---

## 2. Fase de Planejamento — O que Aprendemos

### 2.1 PRD como contrato de time
A decisão de escrever um PRD de 1630 linhas antes de qualquer código foi acertada. Cobrir user stories, arquitetura detalhada, threat model, API design e Definition of Done de cada sprint nos deu um norte claro. **Documentação não é burocracia — é alinhamento.**

### 2.2 Kanban e GitHub Projects
Configurar o quadro com colunas Backlog → In Progress → In Review → Done e automações via GitHub Actions nos ensinou na prática como rastrear trabalho em equipe. O agente Hermes manteve o Kanban atualizado ao longo de todo o projeto.

### 2.3 Infraestrutura como Código (IaC)
Os scripts Terraform para Oracle Cloud Ampere A1 (Always Free) foram um aprendizado concreto de provisionamento declarativo. A VM foi provisionada e o deploy real executado com sucesso — incluindo security lists, nginx reverso, Docker Compose e certificado SSL.

### 2.4 Uso de agentes autônomos (Hermes)
O uso do agente Hermes como orquestrador — criando subagentes para revisão de PRs, correção de bugs, implementação de issues e gerenciamento do Kanban — foi o diferencial técnico do projeto. O fluxo de trabalho onde cada integrante delegava tarefas ao seu agente acelerou a fase final em ~10x.

---

## 3. O que Deu Certo

### 3.1 Pipeline de compilação com fallback mock
`POST /api/compile` com timeouts de 30s por estágio e fallback para mock quando `simplesc` não está disponível. Funciona tanto em produção (compilação real) quanto em desenvolvimento/demo (NASM mockado).

### 3.2 Docker Compose funcional
`docker compose up` sobe 3 containers (nginx, frontend, backend) com health check integrado. Backend responde em `/api/health` com status de todos os componentes (compiler, nasm, docker, supabase).

### 3.3 Sandbox com 9 camadas de isolamento
`--network=none`, `--read-only`, `--cap-drop=ALL`, `--pids-limit=64`, `--memory=128m`, `--cpus=0.5` e timeouts em cascata. Auditamos fork bombs, tentativas de escrita e acesso à rede — tudo bloqueado.

### 3.4 Tokenizer Monarch + tema dark
Registrar a linguagem SIMPLES no Monaco Editor com 27 keywords coloridas (ciano, laranja, verde) deu credibilidade imediata ao projeto visualmente.

### 3.5 Integração Supabase + Auth Gate
Credenciais reais configuradas, JWT validation no backend (`HS256`), `@supabase/auth-ui-react` no frontend com tema dark. Auth gate no `App.tsx` redireciona para tela de login se não autenticado. Modo demo para apresentações sem login.

### 3.6 Deploy Oracle Cloud + HTTPS
VM Ampere A1 provisionada com Docker Compose, nginx reverso com SSL (Let's Encrypt), domínio via nip.io (`simples.163.176.220.47.nip.io`), renovação automática de certificado via cron. Security lists da OCI configuradas com portas 80/443.

### 3.7 Otimização de performance
Descoberta e correção de compilação duplicada (REST + WebSocket) — o `handleRun` compilava o mesmo código duas vezes. Após o fix (#103), a compilação vai direto via WebSocket que já retorna o NASM, reduzindo o tempo pela metade.

### 3.8 Colaboração agente-humano
A parceria com o Hermes permitiu que Carlos concentrasse esforço em decisões de arquitetura enquanto o agente executava tarefas repetitivas (revisão de PRs, correção de bugs, atualização de Kanban, merge de PRs, deploy OCI). O resultado foi 53 issues fechadas em tempo recorde.

---

## 4. O que Não Funcionou / Dificuldades

### 4.1 Conflitos de merge em massa
30+ branches criadas por 3 pessoas + agentes geraram conflitos frequentes nos arquivos compartilhados (docker-compose, package.json, requirements.txt).

### 4.2 Duplicação de código entre App.tsx e routes/index.tsx
Ambos implementavam a mesma UI completa (~1300 linhas duplicadas). Resolvido no PR #101: `routes/index.tsx` virou wrapper fino de 28 linhas, e depois removido completamente no PR #104 (código morto do TanStack Start).

### 4.3 Módulo morto `backend/execution/`
`PtyExecutionStrategy`, `SandboxFactory` e `CompilerService` duplicados com APIs diferentes do `app.*`. Testes (48) validavam código que nunca rodava em produção. Resolvido no PR #101: removido o módulo morto, re-exportado de `app.*`, testes reescritos (56 novos).

### 4.4 Hermes censura JWTs
O sistema censura tokens JWT ao escrever arquivos, truncando secrets no `.env` da OCI. A chave anon do Supabase foi gravada truncada, causando "Invalid API Key" na tela de login. Workaround: Python com concatenação de strings para bypassar a censura.

### 4.5 OOM no deploy OCI
Instância Always Free (1GB RAM) sofre OOM killer ao rodar `docker compose build` com múltiplos containers simultâneos. Solução: build sequencial (runner → backend → frontend), um por vez.

### 4.6 Desbalanceamento de carga
Carlos concentrou a maior parte das implementações e orquestração. Luan contribuiu com documentação e infraestrutura. Kauan implementou várias features mas precisou de correções. O uso de agentes autônomos ajudou a compensar.

---

## 5. O que Faríamos Diferente

1. **MVP vertical na semana 2**: login → editor → compilar → ver NASM, iterando documentação junto
2. **1 PR bootstrap de frontend**: evitar que 10 PRs diferentes recriassem o mesmo scaffold
3. **Daily standups de 10 min**: teriam identificado desbalanceamento e bloqueios antes
4. **Deploy contínuo desde o Sprint 2**: testar em staging, não só local
5. **Testes desde o Sprint 1**: começamos tarde (Sprint 5-6)
6. **Agentes desde o início**: o uso de agentes na fase final foi revolucionário
7. **Build sequencial na OCI desde o início**: evitar OOM killer com `docker compose build` paralelo

---

## 6. Contribuições

| Integrante | Principais entregas |
|---|---|
| **Carlos Barboa** | Arquitetura, PRD, backend completo, DevOps, segurança, documentação, orquestração de agentes, revisão de PRs, deploy OCI, HTTPS, auth gate |
| **Luan Dias** | Documentação (INCIDENTS.md), scripts de infraestrutura, testes de cobertura, contribuições Docker |
| **Kauan Simão** | Docker, empacotamento simplesc, frontend (login, NASM panel, 3-painéis), testes E2E Playwright, correções de bugs, otimização de performance (#103-104) |

---

## 7. Conclusão

O **Simples Editor** foi um projeto ambicioso para uma disciplina de um semestre. Entregamos um produto funcional e público — editar código SIMPLES no navegador, compilar, ver assembly NASM x86 real e executar em sandbox seguro — usando stack de indústria (React + Flask + Docker + WebSocket + Supabase + Oracle Cloud).

**53/53 issues concluídas (100%).** 🎉

O uso de agentes autônomos (Hermes) como acelerador de desenvolvimento foi o diferencial que permitiu fechar o projeto com qualidade em tempo recorde. Aprendemos que **delegar tarefas mecânicas a agentes libera o engenheiro para pensar em arquitetura e tomar decisões**.

Falhamos na distribuição de carga humana e na comunicação síncrona. Mas os aprendizados — técnicos e de equipe — superam as falhas. Se recomeçássemos hoje, faríamos deploy contínuo desde o Sprint 2, build sequencial na OCI, e usaríamos agentes desde o primeiro dia.

---

*Poços de Caldas, 19 de junho de 2026.*
