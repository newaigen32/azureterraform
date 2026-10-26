import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / "python" / "azure_aks_cluster" / "reconcile.py"
SPEC = importlib.util.spec_from_file_location("reconcile_aks", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
reconcile_aks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reconcile_aks)


def valid_configuration() -> dict:
    return {
        "subscription_id": "12345678-1234-1234-1234-123456789abc",
        "location": "Central India",
        "resource_group_name": "aks-learning-rg",
        "cluster_name": "aks-learning",
        "dns_prefix": "aks-learning",
        "sku_tier": "Free",
        "system_node_pool": {
            "name": "system",
            "vm_size": "Standard_D4pls_v5",
            "node_count": 2,
            "os_sku": "Ubuntu",
            "os_disk_type": "Managed",
            "os_disk_size_gb": 64,
            "max_pods": 30,
        },
        "network_profile": {
            "pod_cidr": "10.244.0.0/16",
            "service_cidr": "10.2.0.0/16",
            "dns_service_ip": "10.2.0.10",
        },
        "local_account_disabled": False,
        "enable_container_registry": False,
        "container_registry_name": "uniquelearningacr",
        "enable_container_insights": False,
        "tags": {"environment": "learning", "managed_by": "terraform"},
    }


class ReconcileAksTests(unittest.TestCase):
    def test_accepts_complete_configuration(self) -> None:
        self.assertEqual(
            reconcile_aks.validate_configuration(valid_configuration()), []
        )

    def test_repository_tfvars_example_is_complete(self) -> None:
        configuration = reconcile_aks.load_configuration(
            REPO_ROOT
            / "components"
            / "azure-aks-cluster"
            / "terraform.tfvars.example"
        )
        configuration["subscription_id"] = (
            "12345678-1234-1234-1234-123456789abc"
        )

        self.assertEqual(
            reconcile_aks.validate_configuration(configuration), []
        )

    def test_rejects_pipeline_subscription_mismatch(self) -> None:
        errors = reconcile_aks.validate_configuration(
            valid_configuration(),
            expected_subscription_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        )

        self.assertTrue(any("ARM_SUBSCRIPTION_ID" in error for error in errors))

    def test_reports_missing_required_variable(self) -> None:
        configuration = valid_configuration()
        del configuration["sku_tier"]

        errors = reconcile_aks.validate_configuration(configuration)

        self.assertIn("missing required variable: sku_tier.", errors)

    def test_rejects_placeholder_subscription(self) -> None:
        configuration = valid_configuration()
        configuration["subscription_id"] = (
            "00000000-0000-0000-0000-000000000000"
        )

        errors = reconcile_aks.validate_configuration(configuration)

        self.assertTrue(any("real Azure subscription GUID" in error for error in errors))

    def test_rejects_overlapping_networks(self) -> None:
        configuration = valid_configuration()
        configuration["network_profile"]["service_cidr"] = "10.244.1.0/24"
        configuration["network_profile"]["dns_service_ip"] = "10.244.1.10"

        errors = reconcile_aks.validate_configuration(configuration)

        self.assertTrue(any("must not overlap" in error for error in errors))

    def test_summarizes_create_update_replace_and_delete(self) -> None:
        plan = {
            "resource_changes": [
                {
                    "address": "azurerm_resource_group.aks",
                    "change": {"actions": ["create"]},
                },
                {
                    "address": "module.aks.azurerm_kubernetes_cluster.this",
                    "change": {"actions": ["update"]},
                },
                {
                    "address": "azurerm_container_registry.this[0]",
                    "change": {"actions": ["delete", "create"]},
                },
                {
                    "address": "azurerm_log_analytics_workspace.this[0]",
                    "change": {"actions": ["delete"]},
                },
                {
                    "address": "data.example.unchanged",
                    "change": {"actions": ["read"]},
                },
            ]
        }

        summary = reconcile_aks.summarize_plan(plan)

        self.assertEqual(summary["create"], ["azurerm_resource_group.aks"])
        self.assertEqual(
            summary["update"], ["module.aks.azurerm_kubernetes_cluster.this"]
        )
        self.assertEqual(
            summary["replace"], ["azurerm_container_registry.this[0]"]
        )
        self.assertEqual(
            summary["delete"], ["azurerm_log_analytics_workspace.this[0]"]
        )

    def test_aks_variable_files_do_not_contain_defaults(self) -> None:
        variable_files = (
            REPO_ROOT / "components" / "azure-aks-cluster" / "variables.tf",
            REPO_ROOT / "environments" / "aks-learning" / "variables.tf",
        )

        for variable_file in variable_files:
            self.assertNotIn("default =", variable_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
