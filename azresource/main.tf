resource "azure_resourcegroup" "resource_group" {
  name     = var.resource_group
  location = var.azure_region
  
}