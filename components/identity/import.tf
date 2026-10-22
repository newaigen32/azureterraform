import {
  for_each = module.users.found_users

  to = module.users.azuread_user.managed[each.key]
  id = each.value.object_id
}
