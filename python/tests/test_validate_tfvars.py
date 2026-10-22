import importlib.util
import tempfile
import unittest
from pathlib import Path

from lark.exceptions import LarkError


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_tfvars.py"
SPEC = importlib.util.spec_from_file_location("validate_tfvars", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
validate_tfvars = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_tfvars)


class ValidateTfvarsTests(unittest.TestCase):
    def test_loads_real_identity_tfvars(self) -> None:
        configuration = validate_tfvars.load_configuration(
            REPO_ROOT
            / "components"
            / "identity"
            / "terraform.tfvars"
        )

        self.assertEqual(configuration["users"]["eshwar"], ["developers", "aks_admins"])
        self.assertEqual(validate_tfvars.validate_configuration(configuration), [])

    def test_reports_invalid_hcl_syntax(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            var_file = Path(directory) / "invalid.tfvars"
            var_file.write_text("users = { broken = ", encoding="utf-8")

            with self.assertRaises(LarkError):
                validate_tfvars.load_configuration(var_file)

    def test_accepts_multiple_users_and_groups(self) -> None:
        configuration = {
            "upn_suffix": "trackmyop.in",
            "users": {
                "eshwar": ["developers", "aks_admins"],
                "nalla": ["cloud_admin"],
                "kumar": ["readers"],
            },
        }

        self.assertEqual(validate_tfvars.validate_configuration(configuration), [])

    def test_accepts_valid_rbac_assignment(self) -> None:
        configuration = {
            "users": {"eshwar": ["developers"]},
            "rbac_assignments": {
                "developers_contributor": {
                    "group": "developers",
                    "role_definition_name": "Contributor",
                    "scope": (
                        "/subscriptions/00000000-0000-0000-0000-000000000000/"
                        "resourceGroups/dev-rg"
                    ),
                }
            },
        }

        self.assertEqual(validate_tfvars.validate_configuration(configuration), [])

    def test_rejects_unknown_group(self) -> None:
        errors = validate_tfvars.validate_configuration(
            {"users": {"eshwar": ["developer"]}}
        )

        self.assertTrue(any("unsupported group" in error for error in errors))

    def test_rejects_placeholder_rbac_scope(self) -> None:
        errors = validate_tfvars.validate_configuration(
            {
                "rbac_assignments": {
                    "admins": {
                        "group": "cloud_admin",
                        "role_definition_name": "Owner",
                        "scope": (
                            "/subscriptions/<subscription-id>/"
                            "resourceGroups/<resource-group-name>"
                        ),
                    }
                }
            }
        )

        self.assertTrue(any("scope must be a full Azure" in error for error in errors))

    def test_rejects_duplicate_resolved_upns(self) -> None:
        errors = validate_tfvars.validate_configuration(
            {
                "users": {
                    "eshwar": ["developers"],
                    "nalla": ["cloud_admin"],
                },
                "user_principal_names": {
                    "eshwar": "shared@trackmyop.in",
                    "nalla": "SHARED@trackmyop.in",
                },
            }
        )

        self.assertTrue(any("same UPN" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
