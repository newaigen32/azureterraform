variable "user_group_memberships" {
  description = "Group names for each user, keyed by Terraform user name."
  type        = map(list(string))
  default     = {}
}

variable "user_object_ids" {
  description = "Object IDs of users keyed by user key."
  type        = map(string)
}
