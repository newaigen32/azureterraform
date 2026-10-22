output "group_ids" {
  value = {
    for name, group in azuread_group.groups :
    name => group.object_id
  }
}
