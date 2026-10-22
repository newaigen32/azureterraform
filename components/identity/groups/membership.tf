resource "azuread_group_member" "user_groups" {
  for_each = {
    for membership in flatten([
      for user_name, group_names in var.user_group_memberships : [
        for group_name in toset(group_names) : {
          key        = "${user_name}:${group_name}"
          user_name  = user_name
          group_name = group_name
        }
      ]
    ]) : membership.key => membership
  }

  group_object_id  = azuread_group.groups[each.value.group_name].object_id
  member_object_id = var.user_object_ids[each.value.user_name]
}
