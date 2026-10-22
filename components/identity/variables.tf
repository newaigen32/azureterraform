variable "upn_suffix" {
  description = "Verified Entra domain suffix used to form user principal names."
  type        = string
  default     = "trackmyop.in"

  validation {
    condition     = !startswith(var.upn_suffix, "@") && !strcontains(var.upn_suffix, "@")
    error_message = "Set upn_suffix to a domain such as trackmyop.in, without an @ sign."
  }
}

variable "users" {
  description = "Usernames mapped to the groups each user should join."
  type        = map(list(string))
  default     = {}

  validation {
    condition = alltrue([
      for username in keys(var.users) :
      !strcontains(username, "@") && username == lower(username)
    ])
    error_message = "Use lowercase usernames without an @ sign as the users map keys."
  }

  validation {
    condition = alltrue([
      for group_names in values(var.users) :
      alltrue([
        for group_name in group_names : contains(
          ["cloud_admin", "developers", "readers", "aks_admins"],
          group_name
        )
      ])
    ])
    error_message = "Each user must be assigned to cloud_admin, developers, readers, or aks_admins."
  }
}

variable "user_principal_names" {
  description = "Optional UPN overrides keyed by username, for accounts whose sign-in name differs from username@upn_suffix."
  type        = map(string)
  default     = {}

  validation {
    condition = alltrue([
      for username in keys(var.user_principal_names) : contains(keys(var.users), username)
    ])
    error_message = "Each user_principal_names key must also be present in users."
  }
}

variable "rbac_assignments" {
  description = "Azure RBAC assignments keyed by a unique name. Scopes are Azure resource IDs."
  type = map(object({
    group                = string
    role_definition_name = string
    scope                = string
  }))
  default = {}

  validation {
    condition = alltrue([
      for assignment in values(var.rbac_assignments) :
      contains(["cloud_admin", "developers", "readers", "aks_admins"], assignment.group)
    ])
    error_message = "RBAC assignment groups must be cloud_admin, developers, readers, or aks_admins."
  }
}