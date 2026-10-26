variable "subscription_id" {
  description = "Azure subscription ID used for this environment."
  type        = string
}

variable "location" {
  description = "Azure region for the learning environment."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group created for the AKS learning environment."
  type        = string
}

variable "cluster_name" {
  description = "Name of the AKS cluster."
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
  description = "Required AKS system node pool. D4pls_v5 is an Arm64 SKU."
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
  description = "Whether local Kubernetes administrator credentials are disabled."
  type        = bool
}

variable "enable_container_registry" {
  description = "Create a Basic ACR and grant AcrPull to the AKS kubelet identity."
  type        = bool
}

variable "container_registry_name" {
  description = "Globally unique ACR name used when enable_container_registry is true."
  type        = string
}

variable "enable_container_insights" {
  description = "Create Log Analytics and enable Container Insights. This can consume credits."
  type        = bool
}

variable "tags" {
  description = "Tags applied to environment resources."
  type        = map(string)
}
