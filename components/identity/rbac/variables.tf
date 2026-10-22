variable "assignments" {
  description = "Azure RBAC assignments keyed by a unique name."
  type = map(object({
    group                = string
    role_definition_name = string
    scope                = string
  }))
  default = {}
}

variable "group_ids" {
  description = "Entra security group object IDs, keyed by group name."
  type        = map(string)
}
