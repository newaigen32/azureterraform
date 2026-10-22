output "assignment_ids" {
  description = "Azure resource IDs of the role assignments created by this module."
  value = {
    for name, assignment in azurerm_role_assignment.group_roles :
    name => assignment.id
  }
}
