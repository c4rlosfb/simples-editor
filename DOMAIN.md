# Configuração de Domínio Próprio

> **Nota:** Este é um guia de referência para ser usado **após o deploy da VM na Oracle Cloud** (ver `terraform/README.md` e PRD §14.7). As instruções abaixo pressupõem que a instância OCI já está provisionada e a aplicação está rodando.

Para habilitar a presença pública do **Simples Editor** em um domínio próprio (ex: `simples.seu-dominio.edu.br`), siga as instruções abaixo.

## Pré-requisitos

- [ ] VM OCI Ampere A1 provisionada (via Terraform em `terraform/`)
- [ ] Aplicação rodando na VM (`docker compose up -d`)
- [ ] Domínio registrado com acesso ao painel DNS

## 1. Apontamento de DNS

Acesse o painel do provedor de DNS do seu domínio e crie um registro do tipo **A**:
- **Nome/Host**: `simples` (ou o subdomínio desejado)
- **Tipo**: `A`
- **Valor**: `<IP_PUBLICO_DA_OCI>` (substitua pelo IP da sua instância na Oracle Cloud)
- **TTL**: `Auto` ou `3600`

Aguarde a propagação do DNS (pode levar alguns minutos a algumas horas). Verifique se o domínio já responde ao IP usando ferramentas como `ping` ou `nslookup`.

## 2. Configuração do Nginx e Let's Encrypt (TLS)

Após a propagação, execute os comandos abaixo na instância OCI. Como alternativa, use o script `setup-tls.sh` provisionado pelo cloud-init (`/home/ubuntu/setup-tls.sh`):

```bash
# Opção 1: Script automatizado (recomendado)
sudo DOMAIN=simples.seu-dominio.edu.br EMAIL=admin@seu-dominio.edu.br /home/ubuntu/setup-tls.sh

# Opção 2: Passo a passo manual

```bash
# Instalar certbot
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# Parar o nginx temporariamente
docker compose stop nginx

# Emitir o certificado TLS para o domínio configurado
sudo certbot certonly --standalone -d simples.seu-dominio.edu.br \
     --non-interactive --agree-tos -m admin@seu-dominio.edu.br

# Mover os certificados para a pasta do Nginx
sudo cp /etc/letsencrypt/live/simples.seu-dominio.edu.br/fullchain.pem ./nginx/certs/
sudo cp /etc/letsencrypt/live/simples.seu-dominio.edu.br/privkey.pem ./nginx/certs/

# Reiniciar o Nginx
docker compose start nginx
```

## 3. Renovação Automática

Os certificados do Let's Encrypt expiram a cada 90 dias. Adicione no cronjob para renovação automática:

```bash
echo "0 3 * * * certbot renew --quiet --post-hook 'cd /home/ubuntu/simples-online && docker compose restart nginx'" | sudo crontab -
```

## Validação (Critérios de Aceite)
- [ ] Domínio próprio apontando para o IP da OCI (requer deploy prévio da VM).
- [ ] Domínio resolvendo e acessível publicamente via HTTPS (requer execução do setup-tls.sh).
