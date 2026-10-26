# Python tooling by service

Python automation is grouped by the Azure service or responsibility it manages.

| Folder | Service | Script | Responsibility |
| --- | --- | --- | --- |
| `azure_aks_cluster/` | Azure Kubernetes Service | `reconcile.py` | Validate AKS tfvars, compare Terraform-managed Azure resources, and optionally apply the plan. |
| `identity/` | Microsoft Entra ID and Azure RBAC | `validate_tfvars.py` | Validate users, groups, UPNs, and RBAC scopes before Terraform runs. |
| `tests/azure_aks_cluster/` | AKS tests | `test_reconcile.py` | Test AKS input validation and Terraform plan classification. |
| `tests/identity/` | Identity tests | `test_validate_tfvars.py` | Test identity and RBAC input validation. |

Install the shared dependency once:

```powershell
python -m pip install -r .\python\requirements.txt
```

## AKS commands

The PowerShell wrapper is the normal entry point:

```powershell
.\scripts\aks-lab.ps1 validate
.\scripts\aks-lab.ps1 plan
.\scripts\aks-lab.ps1 reconcile
```

The direct Python equivalents are:

```powershell
python .\python\azure_aks_cluster\reconcile.py --validate-only
python .\python\azure_aks_cluster\reconcile.py
python .\python\azure_aks_cluster\reconcile.py --apply
```

The AKS script reads
`components/azure-aks-cluster/terraform.tfvars` unless `--var-file` is supplied.
Create and update actions require confirmation. Delete and replace actions also
require `--allow-destructive`.

## Identity command

```powershell
python .\python\identity\validate_tfvars.py
```

The identity validator reads `components/identity/terraform.tfvars` unless a
different file is supplied with `--var-file`.
