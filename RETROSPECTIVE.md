# Retrospectiva da Equipe

## O que aprendemos (Fase de Planejamento e Documentação)

Durante a fase inicial do **Simples Editor (Web IDE)**, focada em planejamento e documentação, consolidamos os seguintes aprendizados:

1. **Especificação de produto (PRD)**: Aprendemos a importância de documentar decisões de arquitetura antes de codificar. O PRD de 1630 linhas cobre desde user stories até threat model, servindo como contrato claro para todo o time. Isso nos deu maturidade em engenharia de requisitos.

2. **Planejamento ágil com Kanban**: Configurar o GitHub Project com colunas (Backlog → In Progress → In Review → Done), automações via GitHub Actions e milestones por sprint nos ensinou a estruturar trabalho em equipe com visibilidade e rastreabilidade.

3. **Infraestrutura como Código (IaC)**: A criação dos scripts Terraform para Oracle Cloud Ampere A1 (Always Free) nos deu prática real com provisionamento declarativo de cloud — VCN, subnets, security lists e cloud-init. Entender o modelo de recursos da OCI foi um aprendizado concreto.

4. **Estudo da linguagem SIMPLES e toolchain**: Investigar o compilador `simplesc` (C99 → NASM x86 32-bit), o fluxo `simplesc → nasm → ld → execução` e as 27 palavras reservadas da linguagem consolidou a ponte entre a teoria de Compiladores e a prática de engenharia de software.

5. **Decisões de portabilidade cross-arch**: A pesquisa sobre `qemu-user-static` para rodar binários i386 em hosts ARM64 (Oracle Cloud) e o uso de `binutils-i686-linux-gnu` como alternativa cross-target ao `gcc-multilib` nos ensinou a projetar para múltiplas arquiteturas desde o início.

## Próximos desafios

A implementação dos Sprints 1–5 está por vir: Docker Compose, auth Supabase, Monaco Editor, WebSocket + PTY + xterm.js, e sandbox seguro. A base de documentação que construímos nos dará direção clara para a execução.
