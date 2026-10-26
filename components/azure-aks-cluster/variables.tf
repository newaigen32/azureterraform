variable "cluster_name" {
  description = "Name of the AKS cluster."
  type        = string
}

variable "resource_group_name" {
  description = "Name of the existing resource group that will contain the AKS control-plane resource."
  type        = string
}

variable "location" {
  description = "Azure region in which to deploy AKS."
  type        = string
}

variable "dns_prefix" {
  description = "DNS prefix for the AKS API server."
  type        = string
}

variable "sku_tier" {
  description = "AKS control-plane tier."
  type        = string
}

variable "system_node_pool" {
  description = "Configuration for the required AKS system node pool."
  type = object({
    name            = string
    vm_size         = string
    node_count      = number
    os_sku          = string
    os_disk_type    = string
    os_disk_size_gb = number
    max_pods        = number
  })

}

variable "network_profile" {
  description = "Non-overlapping CIDR ranges used by Azure CNI Overlay."
  type = object({
    pod_cidr       = string
    service_cidr   = string
    dns_service_ip = string
  })

}

variable "local_account_disabled" {
  description = "Disable local Kubernetes admin credentials. Enable only after Entra integration is configured."
  type        = bool
}

variable "container_registry_id" {
  description = "Optional ACR resource ID. When set, the module grants AcrPull to the AKS kubelet identity."
  type        = string
  nullable    = true
}

variable "log_analytics_workspace_id" {
  description = "Optional Log Analytics workspace ID. When set, Container Insights is enabled."
  type        = string
  nullable    = true
}

variable "tags" {
  description = "Tags to apply to the AKS cluster."
  type        = map(string)
}
