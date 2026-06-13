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
6. Reportar veredito

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

## 5. Fase 3 — MERGE (sequencial)

Após revisões aprovadas, mergear em ordem:

```
#62 → #65 → #71 → #72 → #59 → #67 → #68 → #69 → #70 → #73 → #75 → #76 → #77 → #79 → #81
```

Comando: `gh pr merge <NUMERO> --squash --repo c4rlosfb/simples-editor`

⚠️ **Regra:** Só mergear se TODOS os testes passarem e o review estiver aprovado.

---

## 6. Anti-padrões (NÃO FAZER)

- ❌ Aprovar PR próprio
- ❌ Merge sem teste passar
- ❌ Fechar issue antes de TODOS os critérios de aceite cumpridos
- ❌ Criar mais PRs antes de limpar os 22 existentes
- ❌ Commitar `__pycache__/` 

---

## 7. Critérios de Sucesso

- [ ] Todos os PRs designados a você foram revisados
- [ ] Bugs nos seus PRs foram corrigidos
- [ ] PRs aprovados foram mergeados em ordem
- [ ] Kanban atualizado (Done = merged, In Review = PR aberto)
- [ ] `python -m pytest tests/ -v` passa em `dev` após cada merge
