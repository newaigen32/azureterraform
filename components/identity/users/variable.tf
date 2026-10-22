variable "usernames" {
  description = "Lowercase usernames to look up or create."
  type        = list(string)
}

variable "upn_suffix" {
  description = "Verified Entra domain suffix, without an @ sign."
  type        = string
}

variable "user_principal_names" {
  description = "Optional UPN overrides keyed by username."
  type        = map(string)
  default     = {}
}
