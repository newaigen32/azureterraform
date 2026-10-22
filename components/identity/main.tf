module "application" {
  source = "./application"

  owner_object_id = data.azuread_client_config.current.object_id
}

module "groups" {
  source = "./groups"

  user_group_memberships = var.users
  user_object_ids        = module.users.user_ids
}

module "users" {
  source = "./users"

  usernames            = keys(var.users)
  upn_suffix           = var.upn_suffix
  user_principal_names = var.user_principal_names
}

module "rbac" {
  source = "./rbac"

  assignments = var.rbac_assignments
  group_ids   = module.groups.group_ids
}
