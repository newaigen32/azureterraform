resource "azuread_application" "platform" {
  display_name = "platform-app"

  owners = [
    var.owner_object_id
  ]
}
