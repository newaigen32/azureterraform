moved {
  from = azuread_application.platform
  to   = module.application.azuread_application.platform
}

moved {
  from = azuread_application_password.platform
  to   = module.application.azuread_application_password.platform
}

moved {
  from = azuread_service_principal.service_principal
  to   = module.application.azuread_service_principal.service_principal
}

moved {
  from = azuread_group.security_group
  to   = module.groups.azuread_group.groups
}

moved {
  from = module.users.azuread_user.users["alice"]
  to   = module.users.azuread_user.managed["alice"]
}

moved {
  from = module.groups.azuread_group_member.user_groups["alice"]
  to   = module.groups.azuread_group_member.user_groups["alice:developers"]
}
