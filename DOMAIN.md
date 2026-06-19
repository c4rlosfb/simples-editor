# Configuração de Domínio Próprio

> **Status:** ✅ Configurado e funcionando — 19/Jun/2026

## Domínio

| Item | Valor |
|---|---|
| **Domínio** | `simples.163.176.220.47.nip.io` |
| **IP OCI** | `163.176.220.47` |
| **HTTPS** | Let's Encrypt (certbot) |
| **Expira cert** | 16/Set/2026 (renovação automática) |
| **Email** | carlos.barbosa@alunos.ifsuldeminas.edu.br |

## URLs de acesso

| URL | Descrição |
|---|---|
| `https://simples.163.176.220.47.nip.io` | IDE completa |
| `https://simples.163.176.220.47.nip.io/login` | Login Supabase |
| `https://simples.163.176.220.47.nip.io/api/health` | Health check |

> HTTP (porta 80) redireciona automaticamente para HTTPS.

## Como foi configurado

### 1. DNS (nip.io)
`nip.io` é um serviço gratuito de DNS wildcard — qualquer subdomínio no formato `<nome>.<IP>.nip.io` resolve automaticamente para o IP. Zero configuração de DNS necessária.

Verificação:
```bash
nslookup simples.163.176.220.47.nip.io
# → 163.176.220.47
```

### 2. OCI Security List
No OCI Console, adicionar regras de ingresso na subnet pública:
- TCP/80 (HTTP) de 0.0.0.0/0
- TCP/443 (HTTPS) de 0.0.0.0/0

### 3. Let's Encrypt (certbot)
```bash
# Instalar
sudo apt-get install -y certbot

# Parar nginx temporariamente
docker compose stop nginx

# Obter certificado
sudo certbot certonly --standalone \
  -d simples.163.176.220.47.nip.io \
  --non-interactive --agree-tos \
  -m carlos.barbosa@alunos.ifsuldeminas.edu.br

# Copiar para o diretório do nginx
sudo cp /etc/letsencrypt/live/simples.163.176.220.47.nip.io/fullchain.pem ./nginx/certs/
sudo cp /etc/letsencrypt/live/simples.163.176.220.47.nip.io/privkey.pem ./nginx/certs/

# Reiniciar
docker compose up -d nginx
```

### 4. Renovação automática
```bash
echo "0 3 * * * certbot renew --quiet --post-hook 'docker compose -f /home/ubuntu/simples-online/docker-compose.yml restart nginx'" | sudo crontab -
```

## Nginx config (resumo)
- Porta 80: redireciona para HTTPS
- Porta 443: SSL com proxy para frontend:80 e backend:5000
- Certificados montados via volume: `./nginx/certs:/etc/nginx/certs:ro`

## Validação (Critérios de Aceite)
- [x] Domínio próprio apontando para o IP da OCI.
- [x] Domínio resolvendo e acessível publicamente via HTTPS.
