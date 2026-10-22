resource "azuread_service_principal" "service_principal" {
  client_id = azuread_application.platform.client_id
}
