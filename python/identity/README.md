# Identity and RBAC Python validation

`validate_tfvars.py` validates the identity Terraform inputs before deployment:

- Microsoft Entra user names and UPNs;
- supported group memberships;
- duplicate identities; and
- Azure subscription or management-group RBAC scopes.

It validates input only and does not create, update, or delete Azure resources.
