# PRD: Revisão e Correção de PRs — Simples Editor

> **Alvo:** Agentes autônomos (Claude Code, Codex CLI, Hermes, etc.)
> **Perfil:** Engenheiro de Software Sênior Especialista em Code Review
> **Duração esperada:** 15-25 minutos

---

## 1. Objetivo

Revisar os PRs designados a você E corrigir bugs nos seus próprios PRs. Tudo em paralelo via subagentes.

---

## 2. Setup (5 segundos)

```bash
cd caminho/do/simples-editor
git checkout dev && git pull origin dev
```

---

## 3. Fase 1 — REVISAR (paralelo)

Crie **1 subagente por PR** para revisar. Cada subagente deve:

1. `gh pr checkout <NUMERO>` 
2. `gh pr diff <NUMERO>` — analisar código
3. Avaliar: bugs, clareza, DRY/SOLID, performance, cobertura de testes
4. Rodar testes se existirem: `python -m pytest tests/ -v --tb=short`
5. Submeter review: `gh pr review <NUMERO> --approve` ou `--request-changes --body "..."`

### Modelo de review (OBRIGATÓRIO seguir este formato)

```markdown
## Revisão — PR #<NUMERO>

### ✅ Acertos
- [Liste o que está CORRETO e por quê. Seja específico: nome do arquivo, linha, motivo.]
- Ex: "Dockerfile multi-stage bem estruturado (builder stage compila, runtime stage mínimo)"

### 🚨 Erros / Bugs
- [Liste bugs CRÍTICOS que impedem o merge. Arquivo, linha, problema, impacto.]
- Ex: "Porta 8000 em backend/Dockerfile:5 — PRD §14.2 especifica porta 5000"

### ⚠️ Warnings
- [Liste problemas NÃO-bloqueantes. Más práticas, código duplicado, DRY.]
- Ex: "HealthBadge e HealthCheck duplicados em App.tsx — extrair para hook"

### 💡 Implementações / Sugestões
- [Sugestões de melhoria de código, performance, legibilidade.]

### 📊 Resultado dos testes
- [N testes passando, N falhando, cobertura se disponível]

### 🏷️ Veredito
- ✅ APPROVED (se zero bugs críticos)
- ❌ REQUEST CHANGES (se houver bugs críticos)
```

6. Após submeter review: mover issue no Kanban — se APPROVED mantém In Review, se REQUEST CHANGES move para In Progress (`47fc9ee4`)
7. Reportar veredito

### PRs para revisar (substitua pelo seu nome)

**Se você for @LuanCasDias:**
```
#58, #59, #61, #62, #63, #64, #65, #66, #67, #69, #73, #75, #77, #79
```

**Se você for @KauaN-png:**
```
#57, #60, #68, #70, #76, #81
```

### Checklist de revisão (por PR)
- [ ] Nomes de variáveis/funções são semânticos?
- [ ] Código segue DRY/SOLID?
- [ ] Bugs potenciais? (NullPointer, loop infinito, concorrência)
- [ ] Testes passam? Cobertura adequada?
- [ ] Stack bate com PRD? (porta 5000, Flask, Ubuntu 24.04)
- [ ] Keywords SIMPLES corretas? (27 palavras do PRD §13.1)
- [ ] Sem `__pycache__/` versionado?

---

## 4. Fase 2 — CORRIGIR (paralelo)

Crie **1 subagente por bug** para corrigir seus PRs.

### Se você for @KauaN-png — Bugs nos seus PRs:

| PR | Arquivo | Correção |
|---|---|---|
| **#58** | `generate_demo.py` | Substituir keywords erradas: `fimprog→fim`, `declare→(remover)`, `caracter→vazio`, `real→flutuante`, `repita→(remover)`, `:=→<-` |
| **#61** | `App.tsx`, `e2e/tests/*` | Corrigir DEFAULT_CODE e strings SIMPLES nos 5 arquivos de teste |
| **#63** | `Dockerfile` | Substituir `git clone` por COPY de binário pré-compilado |
| **#64** | `Dockerfile` | Mesmo fix do #63 |
| **#66** | `check-contributor.yml` | Trocar `***` por `${{` na linha 18 |

### Se você for @LuanCasDias — Bugs nos seus PRs:

| PR | Arquivo | Correção |
|---|---|---|
| **#71** | — | Nenhum bug. Apenas coordenar com #65 (conflito no INCIDENTS.md). Sugestão: mergear #71 (350 linhas, mais completo) e fechar #65 |
| **#72** | — | Bugs já corrigidos pelo commit `b8fbf39`. Apenas verificar: testes passam? `python -m pytest tests/ -v` |

### Procedimento de correção:
1. `gh pr checkout <NUMERO>`
2. Editar arquivo(s)
3. `git add -A && git commit -m "fix: <descricao>" && git push`
4. PR atualiza automaticamente

---

## 5. Após revisão e correção

⚠️ **NÃO FAÇA MERGE.** Apenas o owner (@c4rlosfb) mergeia.

Quando TODOS os seus PRs estiverem revisados e bugs corrigidos, avise no grupo. O owner fará os merges em sequência, verificando testes a cada passo.

### O que reportar ao owner:
- [ ] Todos os PRs designados a mim foram revisados (aprove/change)
- [ ] Bugs nos meus PRs foram corrigidos e pushados
- [ ] `python -m pytest tests/ -v` passa nos meus branches

---

## 6. Anti-padrões (NÃO FAZER)

- ❌ Fazer merge — apenas o owner mergeia
- ❌ Aprovar PR próprio
- ❌ Merge sem teste passar
- ❌ Fechar issue antes de TODOS os critérios de aceite cumpridos
- ❌ Criar mais PRs antes de limpar os 22 existentes
- ❌ Commitar `__pycache__/` 

---

## 7. Critérios de Sucesso

- [ ] Todos os PRs designados a você foram revisados (approve ou request-changes)
- [ ] Bugs nos seus PRs foram corrigidos e pushados
- [ ] Avisou o owner (@c4rlosfb) que finalizou
- [ ] ⬇️ **DAQUI PRA BAIXO É COM O OWNER** ⬇️
 
- [ ] Owner mergeia PRs aprovados em ordem
- [ ] Owner atualiza Kanban (Done = merged)
- [ ] `python -m pytest tests/ -v` passa em `dev` após cada merge
