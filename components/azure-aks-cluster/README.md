# Azure AKS cluster module

This directory contains the reusable Terraform child module and the AKS input
file requested for the learning environment. It does not configure a provider
or create a resource group; those responsibilities remain in
`environments/aks-learning`.

The module creates:

- one AKS cluster with a required system node pool;
- Azure CNI Overlay networking powered by Cilium;
- a system-assigned cluster identity and kubelet identity;
- OIDC issuer and workload identity support;
- an optional `AcrPull` assignment; and
- optional Container Insights integration.

## Example

```hcl
module "aks" {
  source = "../../components/azure-aks-cluster"

  cluster_name        = "aks-learning"
  resource_group_name = azurerm_resource_group.aks.name
  location            = azurerm_resource_group.aks.location
  dns_prefix          = "aks-learning"
  sku_tier            = "Free"

  system_node_pool = {
    name            = "system"
    vm_size         = "Standard_D4pls_v5"
    node_count      = 2
    os_sku          = "Ubuntu"
    os_disk_type    = "Managed"
    os_disk_size_gb = 64
    max_pods        = 30
  }

  network_profile = {
    pod_cidr       = "10.244.0.0/16"
    service_cidr   = "10.2.0.0/16"
    dns_service_ip = "10.2.0.10"
  }

  local_account_disabled       = false
  container_registry_id        = null
  log_analytics_workspace_id   = null
  tags                         = { environment = "learning" }
}
```

The module deliberately defines no input defaults. Root modules must pass every
value explicitly. For this repository, edit `terraform.tfvars` in this folder.
It is ignored by Git; `terraform.tfvars.example` is the shareable template.

Do not run Terraform from this module directory. The helper scripts execute
Terraform from `environments/aks-learning` and pass this tfvars file explicitly:

```powershell
.\scripts\aks-lab.ps1 validate
.\scripts\aks-lab.ps1 plan
.\scripts\aks-lab.ps1 reconcile
```

`Standard_D4pls_v5` is Arm64. Every workload image scheduled on this pool must
publish a `linux/arm64` image manifest.
