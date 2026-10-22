output "application_id" {
  value = azuread_application.platform.client_id
}

output "service_principal_id" {
  value = azuread_service_principal.service_principal.id
}
