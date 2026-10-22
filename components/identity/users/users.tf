locals {
  requested_upns = {
    for username in var.usernames :
    username => lookup(
      var.user_principal_names,
      username,
      "${username}@${var.upn_suffix}"
    )
  }

  found_users_by_upn = {
    for user in data.azuread_users.requested.users :
    lower(user.user_principal_name) => user
  }

  found_users = {
    for username, upn in local.requested_upns :
    username => local.found_users_by_upn[lower(upn)]
    if contains(keys(local.found_users_by_upn), lower(upn))
  }

  usernames_to_create = toset([
    for username in var.usernames : username
    if !contains(keys(local.found_users), username)
  ])
}

data "azuread_users" "requested" {
  user_principal_names = values(local.requested_upns)
  ignore_missing       = true
}

resource "random_password" "initial" {
  for_each = local.usernames_to_create

  length           = 12
  min_lower        = 1
  min_upper        = 1
  min_numeric      = 1
  min_special      = 1
  override_special = "!@#$%&*()-_=+?"
}

resource "azuread_user" "managed" {
  for_each = local.requested_upns

  display_name = try(
    local.found_users[each.key].display_name,
    title(replace(each.key, "_", " "))
  )
  user_principal_name = try(
    local.found_users[each.key].user_principal_name,
    each.value
  )
  mail_nickname = try(
    local.found_users[each.key].mail_nickname,
    each.key
  )
  account_enabled = try(local.found_users[each.key].account_enabled, true)
  password        = try(random_password.initial[each.key].result, null)

  force_password_change = contains(keys(local.found_users), each.key) ? null : true

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [password, force_password_change]
  }
}
