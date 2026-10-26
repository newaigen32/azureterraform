output "id" {
  description = "Azure resource ID of the AKS cluster."
  value       = azurerm_kubernetes_cluster.this.id
}

output "name" {
  description = "Name of the AKS cluster."
  value       = azurerm_kubernetes_cluster.this.name
}

output "resource_group_name" {
  description = "Resource group containing the AKS cluster."
  value       = azurerm_kubernetes_cluster.this.resource_group_name
}

output "node_resource_group" {
  description = "AKS-managed resource group containing node infrastructure."
  value       = azurerm_kubernetes_cluster.this.node_resource_group
}

output "kubelet_identity_object_id" {
  description = "Object ID of the kubelet managed identity."
  value       = azurerm_kubernetes_cluster.this.kubelet_identity[0].object_id
}

output "oidc_issuer_url" {
  description = "OIDC issuer URL used by AKS workload identity."
  value       = azurerm_kubernetes_cluster.this.oidc_issuer_url
}
