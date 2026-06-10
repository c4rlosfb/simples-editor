---
marp: true
theme: default
class: lead
---

# Simples Editor
**Web IDE para a Disciplina de Compiladores**

---

## O Problema
- Execução de código insegura em ambientes compartilhados.
- Instalação complexa de toolchain (NASM, ld) para alunos.
- Falta de ferramentas focadas no aprendizado de compiladores.

---

## Nossa Solução
- Sandbox seguro baseado em Docker.
- Isolamento rígido de recursos (cgroups, namespaces).
- Interface leve e responsiva com Monaco Editor.
- Comunicação em tempo real via WebSockets.

---

## Arquitetura
- **Frontend**: React + Monaco Editor + xterm.js
- **Backend**: Python (Flask + WebSocket)
- **Infraestrutura**: Docker (sandbox, `--network=none`, limits)

---

## Demonstração
*(Espaço para a demonstração prática da IDE funcionando e da avaliação de segurança do ambiente)*

---

## Próximos Passos
- Salvar histórico de código.
- Modo colaborativo (compartilhar snippet via URL).
- Pool de sandboxes pré-aquecido para latência < 100ms.
- Modo passo-a-passo (debugger).

---

# Obrigado!
