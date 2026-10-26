output "cluster_name" {
  description = "AKS cluster name used by the helper script."
  value       = module.aks.name
}

output "resource_group_name" {
  description = "AKS resource group used by the helper script."
  value       = azurerm_resource_group.aks.name
}

output "node_resource_group" {
  description = "AKS-managed node resource group."
  value       = module.aks.node_resource_group
}

output "container_registry_login_server" {
  description = "ACR login server when the optional registry is enabled."
  value       = try(azurerm_container_registry.this[0].login_server, null)
}

output "connect_command" {
  description = "Azure CLI command used to merge this cluster into the local kubeconfig."
  value       = "az aks get-credentials --resource-group ${azurerm_resource_group.aks.name} --name ${module.aks.name}"
}
