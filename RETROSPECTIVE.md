# Retrospectiva da Equipe

## O que aprendemos (Sprint 6 e fechamento do MVP)

Durante o desenvolvimento do **Simples Editor (Web IDE)**, passamos por desafios significativos e consolidamos diversos aprendizados:

1. **Docker e Sandboxing Seguro**: Aprendemos a importância de isolar execuções de código não-confiável. Configurar o `--network=none`, cgroups (`--cpus`, `--memory`), limitar PIDs e dropar capabilities (`--cap-drop=ALL`) nos deu uma compreensão profunda sobre segurança em containers.
2. **WebSocket e PTY**: A implementação da interação em tempo real com `xterm.js` e a criação de uma bridge para o container via WebSockets nos ajudou a entender melhor a natureza assíncrona das conexões web e a comunicação bidirecional.
3. **Emulação Multi-Arquitetura**: O uso do `qemu-user-static` para rodar binários i386 em hosts ARM64 (como na Oracle Cloud Ampere A1) foi um aprendizado valioso sobre portabilidade e cross-compiling com `binutils-i686-linux-gnu`.
4. **Gerenciamento de Estado no Frontend**: Utilizar React com Monaco Editor nos mostrou como integrar bibliotecas complexas em aplicações modernas, manipulando tokens customizados e syntax highlighting.
5. **Observabilidade e Timeouts**: Implementar limites "wall-clock" rigorosos em várias camadas (no Docker, no Python, e no subprocesso) nos ensinou a focar em *Defense in Depth* para garantir a disponibilidade da aplicação.

Essa jornada consolidou nossos conhecimentos de Engenharia de Software, Infraestrutura (Cloud/Docker) e Compiladores, resultando em um produto funcional e valioso para uso educacional.
