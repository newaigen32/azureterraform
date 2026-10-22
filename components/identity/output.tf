output "client_id" {
  value = data.azurerm_client_config.current.client_id
}

output "object_id" {
  value = data.azuread_client_config.current.object_id
}

output "application_id" {
  value = module.application.application_id
}

output "group_ids" {
  value = module.groups.group_ids
}

output "user_ids" {
  value = module.users.user_ids
}

output "initial_passwords" {
  description = "Generated initial passwords for users created during this run."
  value       = module.users.initial_passwords
  sensitive   = true
}

output "rbac_assignment_ids" {
  description = "Azure resource IDs of the configured RBAC assignments."
  value       = module.rbac.assignment_ids
}

output "service_principal_id" {
  value = module.application.service_principal_id
}