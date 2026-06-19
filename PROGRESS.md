# Progress

## Sprint 1

- [x] feat(docs): add initial README and repo bootstrap
- [x] feat(devops): configure github project board and automations
- [x] feat(devops): define docker compose stack for frontend and backend
- [x] feat(devops): make docker compose up serve the homepage
- [x] feat(backend): configure supabase auth integration
- [x] feat(frontend): add email and password login screen
- [x] feat(backend): add verify_jwt decorator for protected endpoints
- [x] feat(backend): expose api health status endpoint
- [x] feat(devops): validate one merged pr per contributor

## Sprint 2

- [x] feat(frontend): integrate monaco editor on main route
- [x] feat(frontend): register simples language tokenizer with monarch
- [x] feat(frontend): add dark theme with highlighted keywords
- [x] feat(frontend): build three-panel layout with nasm viewer
- [x] feat(frontend): add resizable splitter with double click collapse
- [x] feat(frontend): wire mocked run button for compiling state
- [x] feat(frontend): add readonly nasm monaco panel

## Sprint 3

- [x] feat(backend): package simplesc in backend container
- [x] feat(backend): install binutils i686 linker support
- [x] feat(backend): expose post api compile endpoint
- [x] feat(backend): parse compile errors with line column and phase
- [x] feat(frontend): render compile errors as monaco markers
- [x] feat(frontend): auto populate nasm panel after compile
- [x] feat(backend): enforce compile timeout for pipeline stages

## Sprint 4

- [x] feat(backend): add websocket run endpoint
- [x] feat(frontend): integrate xtermjs terminal panel
- [x] feat(devops): build simples-runner image with qemu-user-static
- [x] feat(backend): implement pty execution strategy
- [x] feat(backend): bridge websocket and pty streams
- [x] feat(backend): support interactive leia end to end
- [x] feat(backend): implement websocket protocol events

## Sprint 5

- [x] feat(frontend): wire stop button to backend stop signal
- [x] feat(backend): enforce wall clock execution timeout
- [x] feat(devops): set docker hard stop timeout
- [x] feat(security): apply sandbox isolation flags
- [x] feat(backend): add per user execution rate limit
- [x] feat(devops): emit structured json logs
- [x] feat(backend): expose prometheus metrics endpoint
- [x] feat(security): audit sandbox escape scenarios
- [x] feat(docs): write sandbox incident response playbook

## Sprint 6

- [ ] feat(frontend): add playwright e2e coverage for core flow
- [ ] feat(backend): reach seventy percent test coverage
- [ ] feat(docs): complete readme with gifs and screenshots
- [ ] feat(docs): produce demo video asset
- [ ] feat(devops): deploy simples editor on oracle cloud ampere a1
- [ ] feat(devops): configure custom domain for optional deployment
- [ ] feat(docs): prepare final presentation materials
- [x] feat(docs): capture team retrospective

---

**Resumo:** 45/53 itens concluídos (85%). Sprints 1-5 integralmente concluídos. Sprint 6 com deploy (#48, #49) bloqueado por credenciais Oracle Cloud e testes E2E/capturas pendentes.
