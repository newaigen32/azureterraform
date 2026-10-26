resource "azurerm_resource_group" "aks" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

resource "azurerm_container_registry" "this" {
  count = var.enable_container_registry ? 1 : 0

  name                = var.container_registry_name
  resource_group_name = azurerm_resource_group.aks.name
  location            = azurerm_resource_group.aks.location
  sku                 = "Basic"
  admin_enabled       = false
  tags                = var.tags
}

resource "azurerm_log_analytics_workspace" "this" {
  count = var.enable_container_insights ? 1 : 0

  name                = "${var.cluster_name}-logs"
  resource_group_name = azurerm_resource_group.aks.name
  location            = azurerm_resource_group.aks.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

module "aks" {
  source = "../../components/azure-aks-cluster"

  cluster_name           = var.cluster_name
  resource_group_name    = azurerm_resource_group.aks.name
  location               = azurerm_resource_group.aks.location
  dns_prefix             = var.dns_prefix
  sku_tier               = var.sku_tier
  system_node_pool       = var.system_node_pool
  network_profile        = var.network_profile
  local_account_disabled = var.local_account_disabled

  container_registry_id = try(azurerm_container_registry.this[0].id, null)
  log_analytics_workspace_id = try(
    azurerm_log_analytics_workspace.this[0].id,
    null
  )

  tags = var.tags
}
