resource "azuread_application_password" "platform" {
  application_id = azuread_application.platform.id
  display_name   = "Terraform Platform Secret"
}
