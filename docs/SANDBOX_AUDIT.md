# Sandbox Security Audit Report

> **Projeto:** Simples Editor
> **Data:** 2026-06-10
> **Responsavel:** Equipe de Seguranca

## Resumo

O sandbox de execucao do Simples Editor foi auditado contra tres superficies
de ataque principais: escrita no filesystem, fork bomb e acesso a rede.
Todas as protecoes estao configuradas e funcionando conforme especificado no PRD.

## Surface de Ataque 1: Escrita no Filesystem

**Configuracao:** `read_only=True` no container Docker.

| Cenario | Resultado Esperado | Resultado Obtido | Status |
|---------|-------------------|------------------|--------|
| Escrever em `/` | Bloqueado | Bloqueado | PASS |
| Escrever em `/tmp` | Permitido (tmpfs) | Permitido | PASS |
| Escrever em `/sandbox` | Bloqueado (bind mount ro) | Bloqueado | PASS |

**Mitigacao:** O container e iniciado com `--read-only`. O unico diretorio
gravavel e `/tmp`, montado como tmpfs com limite de 8MB. O binario compilado
e montado em `/sandbox` no modo `ro` (read-only).

## Surface de Ataque 2: Fork Bomb

**Configuracao:** `pids_limit=64` no container Docker.

| Cenario | Resultado Esperado | Resultado Obtido | Status |
|---------|-------------------|------------------|--------|
| Fork bomb (recursivo) | Contido apos ~64 processos | Contido | PASS |

**Mitigacao:** O limite de 64 processos (PIDs) impede que um programa malicioso
exaura os recursos do host. O `docker run --pids-limit=64` garante que o
container seja morto ao atingir o limite.

## Surface de Ataque 3: Acesso a Rede

**Configuracao:** `network_mode="none"` no container Docker.

| Cenario | Resultado Esperado | Resultado Obtido | Status |
|---------|-------------------|------------------|--------|
| Ping para IP externo | Bloqueado | Bloqueado | PASS |
| HTTP request (wget/curl) | Bloqueado | Bloqueado | PASS |
| DNS lookup | Bloqueado | Bloqueado | PASS |

**Mitigacao:** O container e iniciado com `--network=none`, removendo
completamente a interface de rede. Nenhum trafego de rede e possivel.

## Protecoes Adicionais

| Protecao | Configuracao | Status |
|----------|-------------|--------|
| Memoria maxima | `mem_limit=128m` | Ativo |
| CPU limit | `cpu_quota=50000` (50% de 1 core) | Ativo |
| Usuario nao-root | `user="65534:65534"` (nobody) | Ativo |
| Hard stop timeout | `stop_timeout=12` (SIGKILL apos 12s) | Ativo |
| Timeout de execucao | `asyncio.timeout(10)` (10s) | Ativo |
| Sem privilegios | `--cap-drop=ALL` (implícito) | Ativo |

## Conclusao

O sandbox do Simples Editor esta configurado com todas as protecoes
necessarias para uso em ambiente academico. Nenhuma das superficies de ataque
testadas conseguiu escapar do isolamento do container.

**Classificacao de risco:** BAIXO
**Recomendacao:** Aprovado para uso em turma.

---

## Referencias

- [PRD Secao 11 - Seguranca e Sandboxing](../prd-simples-online.md#11-seguranca-e-sandboxing)
- [PRD Secao 11.4 - Configuracoes de seguranca do container](../prd-simples-online.md#114-configuracoes-de-seguranca-do-container)
- [PRD Secao 11.6 - Threat model resumido](../prd-simples-online.md#116-threat-model-resumido)
- [INCIDENTS.md](./INCIDENTS.md)
