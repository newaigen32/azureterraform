# AKS GitHub Actions setup

The `AKS Terraform` workflow has two stages:

1. Pull requests and pushes to `main` run Python tests, Terraform formatting,
   initialization without a backend, and Terraform validation.
2. A manually dispatched workflow performs an Azure-backed Terraform plan or
   apply through `python/azure_aks_cluster/reconcile.py`.

The deployment job uses OpenID Connect (OIDC). Do not create a client secret.

## 1. Create remote Terraform state

Create an Azure Storage account and private blob container outside the AKS
Terraform configuration. Grant the pipeline identity `Storage Blob Data
Contributor` on the container or storage account.

The pipeline creates `backend.tf` only on the temporary runner and configures
the AzureRM backend from GitHub environment variables. State and saved plans
are not uploaded as workflow artifacts.

## 2. Configure an Azure workload identity

Create a Microsoft Entra application/service principal or user-assigned managed
identity for the workflow. Add a federated credential for this GitHub subject:

```text
repo:<github-owner>/<repository>:environment:aks-learning
```

Grant only the permissions required by this Terraform deployment. The identity
normally needs `Contributor` over the target scope. If ACR integration is
enabled, it also needs permission to create the `AcrPull` role assignment, such
as a narrowly scoped `Role Based Access Control Administrator` assignment.

## 3. Create the GitHub environment

In the GitHub repository, create an environment named `aks-learning`. Add a
required reviewer before enabling apply operations.

Add these environment secrets:

| Secret | Value |
| --- | --- |
| `AZURE_CLIENT_ID` | Client ID of the federated identity. |
| `AZURE_TENANT_ID` | Microsoft Entra tenant ID. |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID. |
| `AKS_TFVARS` | Complete contents of `components/azure-aks-cluster/terraform.tfvars`. |

The `subscription_id` inside `AKS_TFVARS` must match
`AZURE_SUBSCRIPTION_ID`.

Add these environment variables:

| Variable | Example |
| --- | --- |
| `TF_STATE_RESOURCE_GROUP` | `terraform-state-rg` |
| `TF_STATE_STORAGE_ACCOUNT` | `uniquetfstateaccount` |
| `TF_STATE_CONTAINER` | `tfstate` |
| `TF_STATE_KEY` | `aks-learning.tfstate` |

## 4. Run the workflow

Open **Actions → AKS Terraform → Run workflow** and choose:

- `plan` to compare Terraform configuration with the Azure resources recorded
  in remote state;
- `apply` to apply create and update actions; or
- `apply` with `allow_destructive` only after reviewing an intentional delete
  or replacement.

The workflow is serialized with the `aks-learning-terraform` concurrency group
so two state-changing executions cannot run simultaneously.
