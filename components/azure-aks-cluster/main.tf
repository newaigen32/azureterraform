resource "azurerm_kubernetes_cluster" "this" {
  name                = var.cluster_name
  location            = var.location
  resource_group_name = var.resource_group_name
  dns_prefix          = var.dns_prefix

  sku_tier = var.sku_tier

  default_node_pool {
    name            = var.system_node_pool.name
    vm_size         = var.system_node_pool.vm_size
    node_count      = var.system_node_pool.node_count
    os_sku          = var.system_node_pool.os_sku
    os_disk_type    = var.system_node_pool.os_disk_type
    os_disk_size_gb = var.system_node_pool.os_disk_size_gb
    max_pods        = var.system_node_pool.max_pods

    upgrade_settings {
      max_surge = "10%"
    }
  }

  node_provisioning_profile {
    mode = "Manual"
  }

  identity {
    type = "SystemAssigned"
  }

  role_based_access_control_enabled = true
  oidc_issuer_enabled               = true
  workload_identity_enabled         = true
  local_account_disabled            = var.local_account_disabled

  network_profile {
    network_plugin      = "azure"
    network_plugin_mode = "overlay"
    network_data_plane  = "cilium"
    network_policy      = "cilium"
    pod_cidr            = var.network_profile.pod_cidr
    service_cidr        = var.network_profile.service_cidr
    dns_service_ip      = var.network_profile.dns_service_ip
    load_balancer_sku   = "standard"
    outbound_type       = "loadBalancer"
  }

  dynamic "oms_agent" {
    for_each = var.log_analytics_workspace_id == null ? [] : [var.log_analytics_workspace_id]

    content {
      log_analytics_workspace_id = oms_agent.value
    }
  }

  tags = var.tags
}

resource "azurerm_role_assignment" "acr_pull" {
  count = var.container_registry_id == null ? 0 : 1

  scope                            = var.container_registry_id
  role_definition_name             = "AcrPull"
  principal_id                     = azurerm_kubernetes_cluster.this.kubelet_identity[0].object_id
  skip_service_principal_aad_check = true
}
