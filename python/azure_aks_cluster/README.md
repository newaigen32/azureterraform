# Azure AKS Python automation

`reconcile.py` owns the AKS workflow:

1. Load and validate `components/azure-aks-cluster/terraform.tfvars`.
2. Check Terraform formatting and configuration validity.
3. Refresh Terraform state and compare it with Azure.
4. Classify changes as create, update, replace, or delete.
5. Apply the saved plan only when `--apply` is provided and confirmed.

Missing Terraform-managed services are created. Configuration drift is updated
in place when Azure supports it. Replacement and deletion are blocked unless
`--allow-destructive` is provided explicitly.
