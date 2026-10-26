# Azure Terraform learning repository

This repository separates reusable infrastructure modules from deployable
environments. Run Terraform from an environment directory, not from a component
directory.

## Repository layout

```text
components/
  az-resource/             Reusable resource-group module
  azure-aks-cluster/       Reusable AKS module and AKS tfvars
  identity/                Entra users, groups, application, and RBAC stack
environments/
  aks-learning/            Central India AKS learning deployment
scripts/
  aks-lab.ps1              Repeatable AKS lifecycle commands
python/
  azure_aks_cluster/       AKS validation and reconciliation
  identity/                Entra identity and RBAC validation
  tests/                   Tests grouped by the same service names
.github/
  workflows/               GitHub Actions validation and deployment pipeline
```

## AKS flow

```text
components/azure-aks-cluster/terraform.tfvars
      |
      v
python/azure_aks_cluster/reconcile.py
  |-- validates every required input
  |-- refreshes and compares existing Azure state
  |-- creates missing resources and updates drift through Terraform
  |
      v
environments/aks-learning
  |-- configures AzureRM provider
  |-- creates resource group
  |-- optionally creates ACR and Log Analytics
  |
  v
components/azure-aks-cluster
  |-- creates AKS Free-tier control plane
  |-- creates two-node Arm64 system pool
  |-- configures Azure CNI Overlay + Cilium
  |-- enables managed identity, OIDC, and workload identity
  `-- optionally grants AcrPull and enables Container Insights
```

Azure creates the node virtual-machine scale set, disks, load balancer, public
IP, and network resources in a managed resource group whose name begins with
`MC_`.

## Deploy the AKS learning environment

Prerequisites: Terraform 1.7+, Azure CLI, `kubectl`, an Azure subscription, and
Python 3.10+. The example node pool also requires at least eight available
DPLSv5-family vCPUs in Central India.

```powershell
python -m pip install -r .\python\requirements.txt

# Edit components\azure-aks-cluster\terraform.tfvars and replace placeholders.
.\scripts\aks-lab.ps1 validate
.\scripts\aks-lab.ps1 plan
.\scripts\aks-lab.ps1 reconcile
.\scripts\aks-lab.ps1 connect
```

The AKS `variables.tf` files contain no default values. The environment's
single source for all required deployment values is
`components/azure-aks-cluster/terraform.tfvars`. The scripts pass that file to
Terraform while Terraform continues to execute from `environments/aks-learning`.

`validate` checks the tfvars file and Terraform configuration without comparing
Azure resources. `plan` refreshes Terraform state and reports create, update,
replace, and delete actions. `reconcile` runs the same comparison and asks for
confirmation before applying create or update actions.

Deletion and replacement are blocked by default. After reviewing the complete
Terraform plan, explicitly allow them with:

```powershell
.\scripts\aks-lab.ps1 reconcile -AllowDestructive
```

The comparison covers infrastructure managed by this Terraform state. Import an
existing unmanaged Azure resource before reconciliation instead of creating a
second resource with the same name.

## GitHub Actions pipeline

[The AKS workflow](.github/workflows/aks-terraform.yml) automatically runs the
Python tests and Terraform validation for pull requests and pushes to `main`.
Azure plan and apply operations are started manually from the GitHub Actions UI
and use OIDC authentication plus an Azure Storage remote backend.

The pipeline calls the Python reconciler directly and does not depend on the
Windows PowerShell helper. Configure the `aks-learning` GitHub environment by
following [the pipeline setup guide](.github/PIPELINE_SETUP.md).

Stop the lab when it is not in use:

```powershell
.\scripts\aks-lab.ps1 stop
.\scripts\aks-lab.ps1 start
```

Remove the environment when the learning exercise is complete:

```powershell
.\scripts\aks-lab.ps1 destroy
```

## Cost controls

- The example tfvars selects the AKS `Free` tier.
- The example tfvars disables ACR and Container Insights.
- The example tfvars uses two `Standard_D4pls_v5` Arm64 nodes.
- Stop the cluster whenever it is idle; managed disks and networking can still
  incur smaller charges while stopped.
- Every image scheduled on the pool must support `linux/arm64`.

## State

Local state is ignored by Git. For team use, copy
`environments/aks-learning/backend.tf.example` to `backend.tf` and configure an
Azure Storage backend before the first shared deployment.
