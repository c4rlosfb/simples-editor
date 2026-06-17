# PRD: Implementação de Issues — Simples Editor

> **Alvo:** Agentes autônomos | **Perfil:** Engenheiro de Software Sênior
> **Duração:** 10-20 min | **Estratégia:** 1 subagente por issue, paralelo máximo

---

## 1. Setup

```bash
cd caminho/do/simples-editor
git checkout dev && git pull origin dev
```

---

## 2. Fluxo por issue

Para CADA issue da sua lista, siga exatamente:

```
1. git checkout -b fix/issue-<NUMERO>
2. Implementar código (backend/ ou frontend/ ou tests/)
3. ATENÇÃO: Keywords SIMPLES = 27 palavras do PRD §13.1 (NUNCA usar declare, fimprog, caracter, real, :=)
4. ATENÇÃO: Stack = Flask porta 5000, Ubuntu 24.04, React 18, TanStack Start
5. Rodar testes: python -m pytest tests/ -v --tb=short
6. git add -A && git commit -m "feat(scope): descricao (closes #<NUMERO>)"
7. git push -u origin fix/issue-<NUMERO>
8. Criar PR preenchendo OBRIGATORIAMENTE o template do repositório:

```bash
gh pr create --repo c4rlosfb/simples-editor \
  --title "<Título Original da Issue>" \
  --body "## O que muda?
<1-2 frases resumindo as alterações>

## Por quê?
Closes #<NUMERO>

## Como testar?
<Passos para o reviewer reproduzir: comandos, endpoints, testes>

## Checklist
- [x] Testes passando localmente
- [ ] Atualizei o README se necessário
- [ ] Não introduzi breaking changes
- [x] CI verde"
```

9. Mover issue no Kanban para In Review:
```bash
gh project item-edit --id <ITEM_ID> --project-id PVT_kwHOBkrezc4BXzE0 \
  --field-id PVTSSF_lAHOBkrezc4BXzE0zhS9eyQ --single-select-option-id df73e18b
```
(Para descobrir o ITEM_ID: `gh project item-list 3 --owner c4rlosfb --limit 50 --format json | grep <NUMERO>`)
10. Associar reviewer aleatório: `gh pr edit <PR_NUM> --add-reviewer <@LuanCasDias ou @KauaN-png>`
```

---

## 3. Issues por integrante

### @LuanCasDias — 12 issues

| # | Título | Stack | Dica |
|---|---|---|---|
| **#7** | docker compose stack | devops | docker-compose.yml + nginx/ + Dockerfiles. Ver PR #62 como referência |
| **#14** | monaco editor main route | frontend | Integrar @monaco-editor/react na rota / |
| **#18** | resizable splitter | frontend | react-resizable-panels com double-click collapse |
| **#19** | mocked run button | frontend | Botão que mostra "compilando..." sem backend |
| **#24** | parse compile errors | backend | Parser de stderr → {line, column, message, phase} |
| **#26** | auto populate nasm panel | frontend | Após POST /api/compile, preencher painel NASM |
| **#30** | simples-runner image | devops | Dockerfile com qemu-user-static (PRD §14.4) |
| **#32** | bridge ws ↔ pty | backend | Bidirecional: stdout→ws→xterm, stdin←ws←pty |
| **#35** | wire stop button | frontend | Botão Stop → ws.send({type:"stop"}) |
| **#36** | wall clock timeout | backend | asyncio.wait_for(exec, timeout=10) |
| **#39** | rate limit | backend | flask-limiter: 30 exec/min/user |
| **#41** | prometheus metrics | backend | /metrics com histogramas e counters |

### @KauaN-png — 6 issues

| # | Título | Stack | Dica |
|---|---|---|---|
| **#12** | api health endpoint | backend | GET /api/health → {status, version, components} |
| **#16** | dark theme keywords | frontend | Tema Monaco com ciano p/ keywords, laranja p/ números |
| **#17** | three-panel layout | frontend | Editor (esq) + NASM (dir) + Terminal (inf) |
| **#20** | readonly nasm panel | frontend | Monaco em modo 'asm', readOnly: true |
| **#25** | compile errors as markers | frontend | Monaco markers na linha/coluna do erro |
| **#34** | websocket protocol events | backend | Mensagens: compile_started, asm_generated, exec_started, stdout, exit |

---

## 4. Dependências entre issues

```
#7 (docker) → #12 (health) + #14 (monaco)
    ↓
#16 (theme) + #17 (layout) + #18 (splitter)
    ↓
#19 (run btn) + #20 (nasm panel)
    ↓
#24 (errors parser) + #25 (markers) + #26 (populate nasm)
    ↓
#30 (runner img) + #34 (ws protocol)
    ↓
#32 (ws bridge) + #35 (stop btn) + #36 (timeout)
    ↓
#39 (rate limit) + #41 (metrics)
```

Implemente na ordem. Se uma issue depende de código que ainda não existe, deixe o import pronto mas use mock/stub.

---

## 5. Anti-padrões

- ❌ `fimprog`, `declare`, `caracter`, `real`, `repita`, `registros` — NÃO são keywords SIMPLES
- ❌ `:=` — atribuição em SIMPLES é `<-`
- ❌ Porta 8000 — backend é porta 5000
- ❌ `FROM python:3.12-slim` — usar `FROM ubuntu:24.04`
- ❌ `FROM node:22` — React é 18, não 19
- ❌ Commitar `__pycache__/`, `.pytest_cache/`, `node_modules/`
- ❌ Fazer merge

---

## 6. Referências rápidas

- **27 keywords**: programa, inicio, fim, inteiro, flutuante, vazio, se, entao, senao, fimse, enquanto, fimenquanto, para, de, ate, passo, faca, fimpara, leia, escreva, escreval, e, ou, nao, div, procedimento, retorna
- **PRD principal**: `prd-simples-online.md`
- **PRD §8.1**: Stack frontend | **§8.2**: Stack backend | **§13.1**: Monarch tokenizer
- **PRD §14.2**: docker-compose.yml | **§14.3**: backend Dockerfile | **§14.4**: runner Dockerfile
