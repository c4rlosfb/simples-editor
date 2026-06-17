# Configuração do Supabase

O Simples Editor usa Supabase para autenticação JWT. Siga os passos abaixo:

## 1. Criar projeto no Supabase

1. Acesse https://supabase.com e crie uma conta gratuita
2. Crie um novo projeto (Plano Free — 500 MB database)
3. Anote a **Project URL** e a **anon public key**

## 2. Configurar .env

```bash
SUPABASE_URL=https://SEU_PROJETO.supabase.co
SUPABASE_ANON_KEY=sua-chave-anon
SUPABASE_JWT_SECRET=sua-chave-jwt
```

## 3. Modo demonstração (sem Supabase)

Defina `DEMO_MODE=true` no `.env` ou `VITE_DEMO_MODE=true` no frontend.
Neste modo, a autenticação é bypassada — ideal para apresentações.

## 4. Produção

1. Desative o DEMO_MODE
2. Configure as credenciais reais do Supabase
3. O backend valida JWTs automaticamente via `@verify_jwt`
4. O frontend usa `@supabase/auth-ui-react` para login/registro

## Arquitetura de autenticação

```
Usuário → Login (Supabase Auth) → JWT
    → Frontend envia JWT no header Authorization
    → Backend valida JWT com SUPABASE_JWT_SECRET
    → Endpoints protegidos com @require_auth
```
