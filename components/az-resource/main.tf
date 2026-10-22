resource "azurerm_resource_group" "rg" {
  name     = var.rg_name
  location = var.azure_region
}
