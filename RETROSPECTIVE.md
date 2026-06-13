# Retrospectiva da Equipe — Simples Editor

> Disciplina de Compiladores — IFSULDEMINAS Campus Poços de Caldas  
> Engenharia de Computação, 2026/1  
> **Integrantes:** Carlos Barboa, Luan Dias, Kauan Simão

---

## 1. Visão Geral do Projeto

O **Simples Editor** é uma Web IDE para a linguagem didática SIMPLES (27 palavras reservadas em português estruturado), permitindo que alunos escrevam, compilem e executem código diretamente no navegador — com visualização lado-a-lado do assembly NASM x86 32-bit gerado e terminal interativo real. O projeto foi estruturado em 6 sprints, abrangendo desde autenticação até deploy em Oracle Cloud com sandbox seguro.

Ao final do semestre, entregamos um protótipo funcional com pipeline de compilação (`simplesc → nasm → ld → qemu-user-static`), execução interativa via WebSocket + PTY + xterm.js com suporte a `leia`, 9 camadas de isolamento por sandbox, testes E2E com Playwright e documentação abrangente (~3000 linhas entre PRD, README, SPRINTS, guias de deploy e apresentação).

---

## 2. Fase de Planejamento — O que Aprendemos

### 2.1 PRD como contrato de time
A decisão de escrever um PRD de 1630 linhas antes de qualquer código foi acertada. Cobrir user stories, arquitetura detalhada, threat model, API design e Definition of Done de cada sprint nos deu um norte claro. Aprendemos que **documentação não é burocracia — é alinhamento**. Sem o PRD, decisões de arquitetura teriam sido tomadas ad-hoc e gerariam retrabalho.

### 2.2 Kanban e GitHub Projects
Configurar o quadro com colunas Backlog → In Progress → In Review → Done e automações via GitHub Actions nos ensinou na prática como rastrear trabalho em equipe. Porém, subestimamos a disciplina necessária para manter o quadro atualizado — vários itens ficaram desatualizados conforme o escopo real mudava.

### 2.3 Infraestrutura como Código (IaC)
Os scripts Terraform para Oracle Cloud Ampere A1 (Always Free) foram um aprendizado concreto de provisionamento declarativo: VCN, subnets, security lists e cloud-init. Entender o modelo de recursos da OCI — shapes flex, compatibilidade ARM64, regras de firewall em duas camadas (security list + iptables do host) — foi valioso e frustrante em medidas iguais.

### 2.4 Estudo da toolchain SIMPLES
Investigar o compilador `simplesc` (C99 → NASM x86 32-bit), o fluxo `simplesc → nasm -f elf32 → ld -m elf_i386` e as 27 palavras reservadas consolidou a ponte entre teoria de Compiladores e engenharia de software. A pesquisa sobre `qemu-user-static` para emular binários i386 em hosts ARM64 nos forçou a pensar em portabilidade cross-arch desde o dia 1.

---

## 3. Fase de Implementação — O que Deu Certo

### 3.1 Pipeline de compilação robusto (Sprint 3)
O pipeline `POST /api/compile` com timeouts de 15s por estágio (simplesc, nasm, ld) e parsing de erros retornando `{line, column, message, phase}` foi a parte mais sólida do backend. O uso de `binutils-i686-linux-gnu` para cross-linkagem eliminou a dependência de `gcc-multilib` e funciona em qualquer arquitetura de host.

### 3.2 Execução interativa com `leia` (Sprint 4)
Conseguir fazer o fluxo `leia` interativo funcionar end-to-end — WebSocket `/ws/run` → PTY no container → bridge bidirecional → xterm.js — foi o marco técnico mais gratificante. Ver o terminal pedindo input, o usuário digitando e o programa SIMPLES respondendo corretamente validou toda a arquitetura.

### 3.3 Sandbox com 9 camadas de isolamento (Sprint 5)
Implementar `--network=none`, `--read-only`, `--cap-drop=ALL`, `--pids-limit=64`, `--memory=128m`, `--cpus=0.5` e timeouts em cascata nos deu uma noção real de defense in depth. Auditamos fork bombs, tentativas de escrita em `/` e acesso à rede — tudo bloqueado.

### 3.4 Tokenizer Monarch para SIMPLES (Sprint 2)
Registrar a linguagem SIMPLES no Monaco Editor com tokenizer Monarch customizado (27 keywords, comentários `//`, números inteiros) foi mais simples do que esperávamos e o resultado visual — tema dark com highlight — deu credibilidade imediata ao projeto.

### 3.5 Documentação como entregável de primeira classe
README com diagramas ASCII de arquitetura, SPRINTS.md com DoD claro, DOMAIN.md como guia de TLS, PRESENTATION.md em Marp, PROGRESS.md com checklist — a documentação se tornou um ativo real do projeto, não um afterthought.

---

## 4. O que Não Funcionou / Dificuldades Técnicas

### 4.1 WebSocket: bugs críticos de concorrência
O endpoint `/ws/run` nos deu mais trabalho que todo o resto do backend combinado. Tivemos **dual-consumer** (duas corrotinas lendo o mesmo socket simultaneamente), **ip_limiter** quebrando under load e **gevent monkey-patching** causando deadlocks sutis. Foram necessários múltiplos PRs de hotfix para estabilizar. Aprendemos que WebSocket + Python assíncrono exige um cuidado com ciclo de vida de corrotinas que subestimamos.

### 4.2 Terminal flickering no xterm.js
O terminal piscava a cada novo output porque estávamos re-renderizando o buffer inteiro em vez de dar append incremental. O Kauan corrigiu com `append lines instead of re-rendering all`, mas foi uma dor silenciosa que consumiu horas de debugging visual.

### 4.3 Vazamento de diretórios temporários (tempdir leak)
Os containers sandbox criavam diretórios em `/tmp` que não eram limpos após a execução. Em uso contínuo, o disco enchia. Corrigido com cleanup explícito no `finally` do gerenciador de execução, mas foi um daqueles bugs que só aparecem em teste de longa duração.

### 4.4 Integração com Oracle Cloud
A OCI tem duas camadas de firewall (security list + iptables no host Ubuntu) e a documentação oficial é dispersa. Conseguir expor as portas 80/443 levou tentativa e erro. Além disso, o time não chegou a fazer o deploy completo em produção — os scripts Terraform existem, mas a VM nunca foi provisionada de fato para o projeto final.

### 4.5 Desbalanceamento de carga de trabalho
Este foi o problema mais significativo do ponto de vista de equipe. Carlos concentrou ~80% dos commits (47 de 61), incluindo backend, DevOps, segurança e documentação. Kauan contribuiu com infraestrutura, Docker e correções importantes (~10 commits). Luan, responsável pelo frontend, teve apenas 2 commits — o Monaco Editor e os componentes visuais acabaram sendo implementados por Carlos também. Isso gerou frustração e sobrecarga, e é o principal ponto que faríamos diferente.

### 4.6 Itens não concluídos
Vários itens dos sprints ficaram como planejamento sem implementação real:
- Rate limiting por usuário (`flask-limiter`) — configurado mas não testado sob carga
- Métricas Prometheus em `/metrics` — não implementado
- Deploy real em Oracle Cloud — scripts prontos, VM nunca provisionada
- Vídeo de demonstração — planejado, não produzido
- Modo colaborativo e debugger passo-a-passo — ficaram como "próximos passos"

---

## 5. O que Faríamos Diferente

### 5.1 Distribuição de tarefas mais realista
O frontend deveria ter sido dividido em tarefas menores e mais concretas desde o Sprint 1, com pairing sessions obrigatórias. Delegar "frontend inteiro" para um integrante sem experiência prévia em React/Monaco foi um erro de gestão. Faríamos **mob programming** nas primeiras duas semanas para nivelar conhecimento.

### 5.2 Menos documentação inicial, mais código iterativo
O PRD de 1630 linhas foi valioso, mas consumiu as primeiras 3 semanas do projeto. Faríamos um **PRD enxuto** (seções de arquitetura e API) e partiríamos para um **MVP vertical** (login → editor → compilar → ver NASM) na semana 2, iterando a documentação junto com o código.

### 5.3 Testes desde o Sprint 1
Só escrevemos testes (pytest + Playwright) nos sprints 5-6. Se tivéssemos começado com TDD desde o Sprint 1, os bugs de WebSocket teriam sido detectados antes e o refactoring teria sido mais seguro. A meta de 70% de cobertura foi atingida, mas tarde demais para impactar a qualidade do desenvolvimento.

### 5.4 Deploy contínuo em staging
Deveríamos ter provisionado a VM na Oracle Cloud no Sprint 2 e feito deploy contínuo a cada merge. Testar localmente com Docker Compose não revelou os problemas de firewall da OCI, e chegar no Sprint 6 sem deploy real foi frustrante. **Deploy early, deploy often.**

### 5.5 Daily standups reais
Fizemos comunicação majoritariamente assíncrona (GitHub Issues e PRs). Standups de 10 minutos por dia teriam identificado o desbalanceamento de carga e os bloqueios técnicos muito antes.

---

## 6. Contribuições de Cada Integrante

### Carlos Barboa (47 commits)
- **Arquitetura:** Desenho completo da stack (React + Flask + Docker + Supabase), PRD, threat model
- **Backend:** Pipeline de compilação, WebSocket `/ws/run`, `@verify_jwt`, `POST /api/compile`, timeouts, sandbox Docker, structlog, testes unitários
- **DevOps:** Docker Compose, Dockerfiles multi-stage, GitHub Actions, automação do Kanban, scripts Terraform OCI, configuração de domínio/TLS
- **Documentação:** README, SPRINTS.md, PROGRESS.md, DOMAIN.md, PRESENTATION.md, retrospectiva
- **Frontend:** Tokenizer Monarch SIMPLES, integração Supabase Auth, componentes React base

**Autoavaliação:** Assumiu carga desproporcional por necessidade de entregar o projeto, mas reconhece que deveria ter delegado mais e insistido em pairing sessions.

### Luan Dias (2 commits)
- **Documentação:** `INCIDENTS.md` (playbook de resposta a incidentes de sandbox)
- **Backend:** Meta de 70% de cobertura de testes (`pytest --cov`)
- **Responsabilidade planejada:** Frontend, UI/UX, Monaco Editor, componentes React, tema dark

**Autoavaliação:** A baixa participação foi uma combinação de subestimação da complexidade do frontend (React + TanStack Start + Monaco + xterm.js), falta de familiaridade com o stack e comunicação insuficiente para pedir ajuda quando travou.

### Kauan Simão (10 commits)
- **Infraestrutura:** Docker Compose servindo homepage, empacotamento do `simplesc` no container, `binutils-i686-linux-gnu`, linker
- **Qualidade:** Testes E2E com Playwright, validação de PR por contribuidor, auditoria de cenários de escape do sandbox
- **Correções críticas:** Terminal flickering (xterm.js), tempdir leak, stdin writing no WebSocket, fix do noreply email do GitHub

**Autoavaliação:** Contribuiu de forma consistente em infraestrutura e qualidade, mas o escopo de Docker/OCI acabou sendo menor do que o planejado porque o deploy real nunca aconteceu.

---

## 7. Aprendizados Técnicos

1. **WebSocket + Python assíncrono é traiçoeiro:** `asyncio.create_task` com sockets compartilhados, gevent monkey-patching e `flask-sock` têm incompatibilidades sutis. Usar `aiohttp` nativo teria sido mais simples que adaptar Flask.

2. **Docker como sandbox funciona, mas exige defesa em profundidade:** As 9 camadas não são overengineering — cada uma cobre um vetor de ataque que a anterior não cobre. `--network=none` bloqueia exfiltração, mas não bloqueia fork bomb; `--pids-limit` bloqueia fork bomb, mas não bloqueia consumo de CPU; `--cpus` limita CPU, mas não bloqueia syscalls perigosas; etc.

3. **Cross-compilação i386 em ARM64 é viável:** `binutils-i686-linux-gnu` + `qemu-user-static` permitem compilar e rodar binários x86 32-bit em Oracle Cloud Ampere A1 (ARM64) sem emulação de sistema completo. Performance é aceitável para programas didáticos.

4. **Monaco Editor + tokenizer Monarch:** Registrar uma DSL com syntax highlighting é surpreendentemente simples (~80 linhas de configuração Monarch). O ecossistema do Monaco é maduro.

5. **Terraform para OCI tem curva de aprendizado íngreme:** O provider da Oracle é menos documentado que AWS/GCP, e o modelo de compartments + shapes flexíveis é não-intuitivo para quem vem de outras clouds. Mas o tier Always Free (4 OCPUs, 24 GB RAM) é imbatível para projetos acadêmicos.

---

## 8. Aprendizados de Trabalho em Equipe

1. **Comunicação síncrona é insubstituível:** GitHub Issues e PRs são ótimos para rastreamento, mas não substituem uma conversa de 5 minutos para destravar um colega. O hábito de "ficar travado em silêncio" foi o maior inimigo da produtividade do time.

2. **Divisão de tarefas por feature, não por tecnologia:** Dividir "frontend" vs "backend" vs "infra" criou silos. Faríamos melhor dividindo por features verticais (ex: "fluxo de compilação end-to-end" envolvendo os 3) com pairing.

3. **Documentação em excesso pode ser procrastinação:** Passamos tempo demais polindo documentos e tempo de menos codando. O equilíbrio ideal seria 20% documentação, 80% implementação — acabamos em algo próximo de 40/60.

4. **É melhor entregar menos, mas funcionando:** Vários itens dos sprints foram marcados como "feitos" mas não estavam realmente integrados ou testados. Preferiríamos ter 3 features sólidas do que 15 parcialmente implementadas.

---

## 9. Conclusão

O **Simples Editor** foi um projeto ambicioso para uma disciplina de um semestre. Saímos com um protótipo que demonstra o pipeline completo — editar código SIMPLES no navegador, compilar, ver assembly e executar interativamente em sandbox seguro — algo que nenhum de nós tinha feito antes. A stack (React + Flask + Docker + WebSocket + qemu) é realista e próxima do que se usa na indústria.

Falhamos como equipe na distribuição de carga e na comunicação. O projeto foi carregado desproporcionalmente por um integrante, e dois colegas não conseguiram contribuir no nível esperado — por inexperiência técnica, por falta de pairing e por silêncio quando travados. Ironicamente, aprendemos tanto com os erros de trabalho em equipe quanto com os acertos técnicos.

Se recomeçássemos hoje, faríamos: (1) mob programming nas semanas 1-2, (2) MVP vertical na semana 2, (3) deploy contínuo em staging desde o Sprint 2, (4) daily standups de 10 minutos, (5) testes desde o primeiro endpoint. O PRD seria um living document de 300 linhas, não um artefato de 1630 linhas escrito antes de qualquer código.

A experiência reforçou que **engenharia de software é tanto sobre pessoas quanto sobre tecnologia** — e que um time que não se comunica não entrega, independentemente da qualidade da arquitetura.

---

*Poços de Caldas, junho de 2026.*
