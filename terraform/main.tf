terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

variable "tenancy_ocid"     { type = string }
variable "user_ocid"        { type = string }
variable "fingerprint"      { type = string }
variable "private_key_path" { type = string }
variable "region"           { type = string  default = "sa-saopaulo-1" }
variable "compartment_ocid" { type = string }
variable "ssh_public_key"   { type = string }

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

# --- Network ---

resource "oci_core_vcn" "simples" {
  compartment_id = var.compartment_ocid
  cidr_blocks    = ["10.0.0.0/16"]
  display_name   = "simples-online-vcn"
  dns_label      = "simples"
}

resource "oci_core_internet_gateway" "simples" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.simples.id
  display_name   = "simples-igw"
}

resource "oci_core_route_table" "simples" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.simples.id
  display_name   = "simples-rt"
  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.simples.id
  }
}

resource "oci_core_security_list" "simples" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.simples.id
  display_name   = "simples-sl"

  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
  }

  # SSH — restringir ao seu IP em produção
  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6"
    tcp_options { min = 22  max = 22 }
  }
  # HTTP (redirect para HTTPS via nginx)
  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6"
    tcp_options { min = 80  max = 80 }
  }
  # HTTPS
  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "6"
    tcp_options { min = 443 max = 443 }
  }
}

resource "oci_core_subnet" "simples" {
  compartment_id      = var.compartment_ocid
  vcn_id              = oci_core_vcn.simples.id
  cidr_block          = "10.0.1.0/24"
  display_name        = "simples-public-subnet"
  route_table_id      = oci_core_route_table.simples.id
  security_list_ids   = [oci_core_security_list.simples.id]
  prohibit_public_ip_on_vnic = false
}

# --- Compute (Always Free Ampere A1) ---

data "oci_core_images" "ubuntu_2204_arm" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  shape                    = "VM.Standard.A1.Flex"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

resource "oci_core_instance" "simples" {
  availability_domain = data.oci_identity_availability_domain.ad.name
  compartment_id      = var.compartment_ocid
  display_name        = "simples-online"
  shape               = "VM.Standard.A1.Flex"

  shape_config {
    ocpus         = 2     # Always Free permite até 4
    memory_in_gbs = 12    # Always Free permite até 24
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.ubuntu_2204_arm.images[0].id
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.simples.id
    assign_public_ip = true
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data           = base64encode(file("${path.module}/cloud-init.yaml"))
  }
}

data "oci_identity_availability_domain" "ad" {
  compartment_id = var.tenancy_ocid
  ad_number      = 1
}

output "public_ip" {
  value = oci_core_instance.simples.public_ip
}
