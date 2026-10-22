output "user_ids" {
  value = {
    for name, user in azuread_user.managed : name => user.object_id
  }
}

output "found_users" {
  value = local.found_users
}

output "initial_passwords" {
  description = "Generated initial passwords for users created during this run."
  value = {
    for name, password in random_password.initial : name => password.result
  }
  sensitive = true
}
