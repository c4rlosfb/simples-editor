---
marp: true
theme: default
class: lead
footer: "IFSULDEMINAS — Campus Poços de Caldas"
---

# Simples Editor — Web IDE para a Linguagem SIMPLES

**IFSULDEMINAS — Campus Poços de Caldas — Compiladores**

Carlos Barboa, Luan Dias, Kauan Simão  
2026

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

<!-- _footer: "IFSULDEMINAS — Campus Poços de Caldas | Demo ao vivo" -->

### Fluxo da Demo ao Vivo

1. **Editor**: escrita de código SIMPLES no Monaco Editor com syntax highlighting.
2. **Compilação**: envio do código ao backend; compilador traduz para assembly NASM.
3. **Montagem & Linkedição**: NASM + ld produzem executável dentro do container sandbox.
4. **Execução**: saída exibida em tempo real no terminal xterm.js integrado.
5. **Segurança**: demonstração das barreiras de isolamento (`--network=none`, limites de CPU/memória, filesystem efêmero).

*(Screenshots da interface serão inseridas aqui)*

---

## Próximos Passos
- Salvar histórico de código.
- Modo colaborativo (compartilhar snippet via URL).
- Pool de sandboxes pré-aquecido para latência < 100ms.
- Modo passo-a-passo (debugger).

---

<!-- _class: lead -->

# Obrigado!

**Simples Editor** — Web IDE para a Linguagem SIMPLES

https://github.com/c4rlosfb/simples-editor

Carlos Barboa — [@c4rlosfb](https://github.com/c4rlosfb)  
Luan Dias — [@LuanCasDias](https://github.com/LuanCasDias)  
Kauan Simão — [@KauaN-png](https://github.com/KauaN-png)
