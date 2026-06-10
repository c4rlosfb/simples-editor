# Terraform — Deploy Oracle Cloud Infrastructure (Ampere A1)

Provisiona a infraestrutura para o Simples Editor na Oracle Cloud, usando instância
**Ampere A1 (ARM64)** do tier Always Free.

## Pré-requisitos

1. Conta Oracle Cloud Infrastructure com acesso ao compartment alvo.
2. API key configurada (ver [documentação OCI](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm)).
3. Par de chaves SSH para acesso à VM.
4. [Terraform CLI](https://developer.hashicorp.com/terraform/downloads) ≥ 1.5.

## Configuração

Crie `oci.tfvars` (nunca commitar — está no `.gitignore`):

```hcl
tenancy_ocid     = "ocid1.tenancy.oc1..xxxxxxxx"
user_ocid        = "ocid1.user.oc1..xxxxxxxx"
fingerprint      = "xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx"
private_key_path = "~/.oci/oci_api_key.pem"
region           = "sa-saopaulo-1"
compartment_ocid = "ocid1.compartment.oc1..xxxxxxxx"
ssh_public_key   = "ssh-rsa AAAAB3NzaC1yc2E..."
```

## Deploy

```bash
cd terraform
terraform init
terraform plan  -var-file="oci.tfvars"
terraform apply -var-file="oci.tfvars"
```

## Pós-deploy

Após o `apply`, acesse a VM:

```bash
ssh ubuntu@$(terraform output -raw public_ip)
```

### Próximos passos na VM

1. **Clonar o repositório e subir a aplicação** (ver PRD §14.7.4):
   ```bash
   git clone --recurse-submodules https://github.com/c4rlosfb/simples-editor.git ~/simples-online
   cd ~/simples-online
   cp .env.example .env
   # editar .env com credenciais Supabase
   docker compose up --build -d
   ```

2. **Configurar TLS** (após apontar domínio para o IP público):
   ```bash
   sudo DOMAIN=simples.seu-dominio.edu.br EMAIL=admin@seu-dominio.edu.br /home/ubuntu/setup-tls.sh
   ```

## Recursos provisionados

| Recurso | Descrição |
|---|---|
| `oci_core_vcn` | VCN `10.0.0.0/16` com DNS label `simples` |
| `oci_core_subnet` | Subnet pública `10.0.1.0/24` |
| `oci_core_internet_gateway` | Internet Gateway para tráfego de saída |
| `oci_core_security_list` | Portas 22 (SSH), 80 (HTTP), 443 (HTTPS) |
| `oci_core_instance` | VM.Standard.A1.Flex: 2 OCPU, 12 GB RAM, Ubuntu 22.04 ARM64 |

## Destruir

```bash
terraform destroy -var-file="oci.tfvars"
```

> **Atenção:** O destroy remove a VM e todos os dados. Faça backup do que for necessário antes.
