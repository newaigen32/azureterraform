module "dev_rg" {
  source = "./modules/az-resource"

  rg_name      = var.rg_name
  azure_region = var.azure_region
}