---
marp: true
theme: default
class: lead
---

# Simples Editor
**Web IDE para Educação e Entrevistas**

---

## O Problema
- Execução de código insegura em ambientes compartilhados.
- Dificuldade na avaliação técnica de candidatos.
- Falta de ferramentas simples e focadas no básico.

---

## Nossa Solução
- Sandbox seguro baseado em Docker.
- Isolamento rígido de recursos (cgroups, namespaces).
- Interface leve e responsiva com Monaco Editor.
- Comunicação em tempo real via WebSockets.

---

## Arquitetura
- **Frontend**: React + Monaco Editor + xterm.js
- **Backend**: Python (FastAPI/Flask)
- **Infraestrutura**: Docker (Restrito, `--network=none`, limits)

---

## Demonstração
*(Espaço para a demonstração prática da IDE funcionando e da avaliação de segurança do ambiente)*

---

## Próximos Passos
- Suporte a mais linguagens.
- Modo colaborativo.
- Histórico de execuções.

---

# Obrigado!
