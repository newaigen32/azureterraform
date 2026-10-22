resource "azuread_group" "groups" {
  for_each = local.groups

  display_name     = each.value.name
  security_enabled = true
}
