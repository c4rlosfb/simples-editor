# Progress

## Sprint 1

- [ ] feat(docs): add initial README and repo bootstrap
- [ ] feat(devops): configure github project board and automations
- [ ] feat(devops): define docker compose stack for frontend and backend
- [ ] feat(devops): make docker compose up serve the homepage
- [ ] feat(backend): configure supabase auth integration
- [ ] feat(frontend): add email and password login screen
- [ ] feat(backend): add verify_jwt decorator for protected endpoints
- [ ] feat(backend): expose api health status endpoint
- [ ] feat(devops): validate one merged pr per contributor

## Sprint 2

- [ ] feat(frontend): integrate monaco editor on main route
- [ ] feat(frontend): register simples language tokenizer with monarch
- [ ] feat(frontend): add dark theme with highlighted keywords
- [ ] feat(frontend): build three-panel layout with nasm viewer
- [ ] feat(frontend): add resizable splitter with double click collapse
- [ ] feat(frontend): wire mocked run button for compiling state
- [ ] feat(frontend): add readonly nasm monaco panel

## Sprint 3

- [ ] feat(backend): package simplesc in backend container
- [ ] feat(backend): install binutils i686 linker support
- [ ] feat(backend): expose post api compile endpoint
- [ ] feat(backend): parse compile errors with line column and phase
- [ ] feat(frontend): render compile errors as monaco markers
- [ ] feat(frontend): auto populate nasm panel after compile
- [ ] feat(backend): enforce compile timeout for pipeline stages

## Sprint 4

- [ ] feat(backend): add websocket run endpoint
- [ ] feat(frontend): integrate xtermjs terminal panel
- [ ] feat(devops): build simples-runner image with qemu-user-static
- [ ] feat(backend): implement pty execution strategy
- [ ] feat(backend): bridge websocket and pty streams
- [ ] feat(backend): support interactive leia end to end
- [ ] feat(backend): implement websocket protocol events

## Sprint 5

- [ ] feat(frontend): wire stop button to backend stop signal
- [x] feat(backend): enforce wall clock execution timeout
- [x] feat(devops): set docker hard stop timeout
- [x] feat(security): apply sandbox isolation flags
- [ ] feat(backend): add per user execution rate limit
- [ ] feat(devops): emit structured json logs
- [ ] feat(backend): expose prometheus metrics endpoint
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
- [ ] feat(docs): capture team retrospective
