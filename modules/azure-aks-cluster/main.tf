resource "azurerm_resource_group" "resource_group" {
  name     = var.resource_group
  location = var.azure_region
}

resource "azurerm_aks_kubernetes_cluster" "aks_cluster" {
  name                = var.cluster_name
  location            = azurerm_resource_group.resource_group.location
  resource_group_name = azurerm_resource_group.resource_group.name
  dns_prefix          = var.dns_prefix

  default_node_pool {
    name       = "default"
    node_count = var.node_count
    vm_size    = var.vm_size
  }

  identity {
    type = "SystemAssigned"
  }
  
}

resource "azurerm_node_pool" "np" {
  name                = var.node_pool_name
  kubernetes_cluster_id = azurerm_aks_kubernetes_cluster.aks_cluster.id
  vm_size             = var.node_pool_vm_size
  node_count          = var.node_pool_node_count
  os_type             = var.node_pool_os_type
  mode                = "User"
}
