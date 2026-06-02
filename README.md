# Simples Editor

**Simples Editor** é uma IDE web que permite escrever, compilar e executar programas na linguagem **SIMPLES** diretamente no navegador, sem nenhuma instalação local. 

O ambiente conta com três painéis:
- **Editor SIMPLES**: code editor com syntax highlighting.
- **Painel NASM x32**: mostra o assembly gerado em tempo real.
- **Terminal interativo**: emulador de terminal (xterm.js) para input/output real.

## Como começar (Ambiente de Desenvolvimento)

### Pré-requisitos
- Docker Engine 24+ ou Docker Desktop
- Docker Compose v2
- Conta no Supabase (para gerenciar a autenticação)

### Passo a passo para rodar localmente

1. Clone o repositório (com submodules):
   ```bash
   git clone --recurse-submodules https://github.com/c4rlosfb/simples-editor.git
   cd simples-editor
   ```

2. Configure as variáveis de ambiente:
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas credenciais do Supabase
   ```

3. Suba os containers:
   ```bash
   docker compose up --build -d
   ```

4. Acesse no navegador:
   - Frontend: `http://localhost`
   - Backend health check: `http://localhost/api/health`

Consulte a documentação técnica principal (`prd-simples-online.md`) para obter mais informações de arquitetura e infraestrutura.