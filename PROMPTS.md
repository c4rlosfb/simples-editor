# Prompts para Agentes — Simples Editor

> Cole o bloco correspondente ao seu nome no agente (Claude Code, Codex, Hermes, etc.)
> Os PRDs contém instruções detalhadas de formato de review e template de PR.

---

## @LuanCasDias

### Tarefa 1: Revisar PRs + Corrigir Bugs
```
Leia PRD-AGENTES.md. Sou @LuanCasDias.
Execute Fase 1 (REVISAR) e Fase 2 (CORRIGIR) para minha lista.

⚠️ REGRAS:
- Use o MODELO DE REVIEW do PRD (✅ Acertos, 🚨 Erros, ⚠️ Warnings, 💡 Sugestões)
- Após submeter review, mova a issue no Kanban (APPROVED → In Review, REQUEST CHANGES → In Progress)
- NÃO faça merge — apenas o owner mergeia.
- NÃO aprove PR próprio.

Crie subagentes sêniores. Trabalhe em paralelo.
```

### Tarefa 2: Implementar Issues
```
Leia PRD-ISSUES.md. Sou @LuanCasDias.
Implemente as 12 issues da minha lista em ordem de dependência.

⚠️ REGRAS:
- Ao criar PR, preencha OBRIGATORIAMENTE o template (O que muda?, Por quê?, Como testar?, Checklist)
- Após criar PR, mova a issue para In Review no Kanban
- Associe reviewer aleatório (@KauaN-png ou @c4rlosfb)
- 1 subagente por issue. NÃO faça merge.
```

---

## @KauaN-png

### Tarefa 1: Revisar PRs + Corrigir Bugs
```
Leia PRD-AGENTES.md. Sou @KauaN-png.
Execute Fase 1 (REVISAR) e Fase 2 (CORRIGIR) para minha lista.

⚠️ REGRAS:
- Use o MODELO DE REVIEW do PRD (✅ Acertos, 🚨 Erros, ⚠️ Warnings, 💡 Sugestões)
- Após submeter review, mova a issue no Kanban (APPROVED → In Review, REQUEST CHANGES → In Progress)
- NÃO faça merge — apenas o owner mergeia.
- NÃO aprove PR próprio.

Crie subagentes sêniores. Trabalhe em paralelo.
```

### Tarefa 2: Implementar Issues
```
Leia PRD-ISSUES.md. Sou @KauaN-png.
Implemente as 6 issues da minha lista em ordem de dependência.

⚠️ REGRAS:
- Ao criar PR, preencha OBRIGATORIAMENTE o template (O que muda?, Por quê?, Como testar?, Checklist)
- Após criar PR, mova a issue para In Review no Kanban
- Associe reviewer aleatório (@LuanCasDias ou @c4rlosfb)
- 1 subagente por issue. NÃO faça merge.
```

---

## @c4rlosfb (Owner)

### Quando Luan e Kauan finalizarem as revisões:
```
Leia PRD-AGENTES.md. Sou @c4rlosfb, owner.
Execute Fase 3: mergear PRs aprovados em ordem (ver seção 5).

⚠️ REGRAS:
- Merge UM por vez: gh pr merge <NUMERO> --squash
- Após cada merge: python -m pytest tests/ -v
- Se testes quebrarem: reverter e reportar
- Mover issue para Done no Kanban após merge
```
