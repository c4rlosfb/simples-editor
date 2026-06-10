# Incident Response Playbook - Simples Editor

> **Proposito:** Procedimentos para detectar, conter e mitigar incidentes
> de seguranca no ambiente Simples Editor.

## Niveis de severidade

| Nivel | Descricao | Exemplo |
|-------|-----------|---------|
| **SEV-3** | Baixo impacto, sem dados expostos | Aluno consegue ler `/etc/passwd` do container |
| **SEV-2** | Impacto moderado, acesso nao autorizado | Aluno consegue executar comandos no host Docker |
| **SEV-1** | Impacto critico, dados de usuarios expostos | Aluno acessa dados de outro usuario ou do Supabase |

---

## Procedimento SEV-3: Leitura nao autorizada dentro do sandbox

### Sintomas
- Aluno relata que conseguiu ler arquivos fora do diretorio `/sandbox`
- Logs mostram tentativas de `cat /etc/passwd`, `ls /root`, etc.

### Passos
1. Verificar se a flag `--read-only` esta ativa no container
2. Verificar se o bind mount do binario esta em modo `ro`
3. Testar com o script `scripts/test-sandbox.sh`
4. Se confirmado, reiniciar o backend e notificar a equipe

---

## Procedimento SEV-2: Escape parcial do sandbox

### Sintomas
- Consumo excessivo de CPU/memoria no host
- Processos filhos do Docker com usuario nobody
- Tentativas de fork bomb ou network scan

### Passos
1. Imediatamente: `docker kill` em todos os containers suspeitos
2. Verificar limites: `docker inspect <container> | grep -A5 PidsLimit`
3. Verificar logs do backend em busca do IP do usuario
4. Bloquear usuario temporariamente (rate limit)
5. Executar auditoria completa: `bash scripts/test-sandbox.sh`
6. Documentar descobertas neste arquivo

---

## Procedimento SEV-1: Escape critico do sandbox

### Sintomas
- Aluno executa comandos como root no host
- Acesso a variaveis de ambiente com chaves do Supabase
- Modificacao de dados de outro usuario

### Passos
1. **IMEDIATAMENTE:** Desligar o servico: `docker compose down`
2. Rotacionar todas as chaves (Supabase JWT_SECRET, API keys)
3. Isolar o host da rede interna
4. Coletar evidencias: logs do Docker, historico de execucoes
5. Notificar o professor/orientador
6. Investigar causa raiz antes de religar
7. Atualizar este documento com a licao aprendida

---

## Contatos

| Papel | Responsavel |
|-------|-------------|
| Desenvolvedor backend | @c4rlosfb |
| DevOps/infra | @KauaN-png |
| Professor/orientador | Prof. da disciplina |

---

## Historico de incidentes

| Data | Severidade | Descricao | Resolucao |
|------|------------|-----------|-----------|
| - | - | Nenhum incidente registrado ate o momento | - |
