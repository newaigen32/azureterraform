resource "azurerm_role_assignment" "group_roles" {
  for_each = var.assignments

  scope                = each.value.scope
  role_definition_name = each.value.role_definition_name
  principal_id         = var.group_ids[each.value.group]
  principal_type       = "Group"
}
