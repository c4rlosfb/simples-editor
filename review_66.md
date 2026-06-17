## Revisão do PR #66 — feat(devops): validate one merged pr per contributor

### ❌ Request Changes

#### 🔴 CRÍTICO: Syntax error no `check-contributor.yml`
A linha 17 contém um erro de sintaxe nos workflows:
```
AUTHOR=*** github.event.pull_request.user.login }}"
```
A expressão `${{ }}` do GitHub Actions está corrompida (aparece como `***`). Isso **quebra o workflow completamente** — o Actions nem vai conseguir parsear o YAML.

**Correção:**
```
AUTHOR="${{ github.event.pull_request.user.login }}"
```

#### 🟡 Lógica incorreta no `check-contributor.yml`
A condição:
```
if [ "$COUNT" -ge 1 ] || [ "$(gh pr view ${{ github.event.pull_request.number }} --json merged --jq '.merged')" = "true" ]
```
A segunda parte verifica se o PR atual está merged. Mas este workflow dispara em `opened`/`reopened` — o PR nunca estará merged nesse ponto. Esta verificação nunca será verdadeira.

**Ação:** Remover a segunda condição ou ajustar a lógica.

#### 🟡 `validate-pr-coverage.yml`: `while read` com `gh pr list`
O loop `while IFS='|' read` usa pipe, e dentro dele `gh pr list` é chamado. O `gh` CLI pode consumir stdin do pipe, causando processamento incorreto. O `</dev/null` foi adicionado em uma das chamadas mas não na outra.

**Ação:** Adicionar `</dev/null` a todas as chamadas `gh` dentro do loop, ou reestruturar para evitar o pipe.

#### 🟡 `validate-pr-coverage.yml`: extração frágil de login
A extração do login via `noreply` email:
```
login="${email#*+}"
login="${login%@*}"
```
Isso extrai o ID numérico (ex: `U_kgDOCyHJ9Q`), não o username GitHub (`KauaN-png`). O `gh pr list --author` espera o username, não o ID.

**Ação:** Testar com usernames reais ou usar a GitHub API para resolver IDs → usernames.

#### 🟡 `check-contributor.yml`: Sempre retorna exit code 0
O workflow nunca falha (`exit 1`) — ele apenas imprime WARNING. Se o objetivo é "validate one merged PR per contributor" e bloquear PRs sem contribuição prévia, o workflow deveria falhar (`exit 1`) quando `COUNT` for 0.

### ✅ Acertos
- `validate-pr-coverage.yml` com schedule semanal + trigger manual ✅
- `check-contributor.yml` escuta eventos `opened`/`reopened` corretamente ✅
- PR template atualizado com checkbox de primeira contribuição ✅
- `PROGRESS.md` atualizado ✅
- Uso de `gh` CLI para queries da GitHub API ✅
- Estrutura YAML dos workflows bem organizada ✅

### Ação
Corrigir o erro de sintaxe crítico no `check-contributor.yml`, ajustar a lógica de verificação de merge, corrigir extração de login no `validate-pr-coverage.yml`, e adicionar `exit 1` para PRs sem contribuição prévia.
