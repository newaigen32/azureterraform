"""Validate and reconcile the Azure AKS Terraform environment."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import hcl2
from hcl2 import SerializationOptions
from lark.exceptions import LarkError


SUBSCRIPTION_ID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$"
)
NODE_POOL_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]{0,11}$")
ACR_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9]{5,50}$")

REQUIRED_VARIABLES = {
    "subscription_id",
    "location",
    "resource_group_name",
    "cluster_name",
    "dns_prefix",
    "sku_tier",
    "system_node_pool",
    "network_profile",
    "local_account_disabled",
    "enable_container_registry",
    "container_registry_name",
    "enable_container_insights",
    "tags",
}


def load_configuration(var_file_path: Path) -> dict[str, Any]:
    with var_file_path.open(encoding="utf-8") as var_file:
        configuration = hcl2.load(
            var_file,
            serialization_options=SerializationOptions(
                with_comments=False,
                strip_string_quotes=True,
            ),
        )
    if not isinstance(configuration, dict):
        raise ValueError("variable file must contain a top-level map")
    return configuration


def _validate_non_empty_string(
    configuration: dict[str, Any], key: str, errors: list[str]
) -> None:
    value = configuration.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{key} must be a non-empty string.")


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_configuration(
    configuration: dict[str, Any], expected_subscription_id: str | None = None
) -> list[str]:
    errors: list[str] = []

    for key in sorted(REQUIRED_VARIABLES - configuration.keys()):
        errors.append(f"missing required variable: {key}.")

    for key in (
        "location",
        "resource_group_name",
        "cluster_name",
        "dns_prefix",
    ):
        _validate_non_empty_string(configuration, key, errors)

    subscription_id = configuration.get("subscription_id")
    if (
        not isinstance(subscription_id, str)
        or not SUBSCRIPTION_ID_PATTERN.fullmatch(subscription_id)
        or subscription_id == "00000000-0000-0000-0000-000000000000"
    ):
        errors.append("subscription_id must be a real Azure subscription GUID.")
    elif (
        expected_subscription_id
        and subscription_id.casefold() != expected_subscription_id.casefold()
    ):
        errors.append(
            "subscription_id must match the ARM_SUBSCRIPTION_ID used by the pipeline."
        )

    sku_tier = configuration.get("sku_tier")
    if sku_tier not in {"Free", "Standard", "Premium"}:
        errors.append("sku_tier must be Free, Standard, or Premium.")

    for key in (
        "local_account_disabled",
        "enable_container_registry",
        "enable_container_insights",
    ):
        if not isinstance(configuration.get(key), bool):
            errors.append(f"{key} must be true or false.")

    node_pool = configuration.get("system_node_pool")
    if not isinstance(node_pool, dict):
        errors.append("system_node_pool must be an object.")
    else:
        required_pool_keys = {
            "name",
            "vm_size",
            "node_count",
            "os_sku",
            "os_disk_type",
            "os_disk_size_gb",
            "max_pods",
        }
        for key in sorted(required_pool_keys - node_pool.keys()):
            errors.append(f"system_node_pool is missing {key}.")

        name = node_pool.get("name")
        if not isinstance(name, str) or not NODE_POOL_NAME_PATTERN.fullmatch(name):
            errors.append(
                "system_node_pool.name must be 1-12 lowercase alphanumeric "
                "characters and start with a letter."
            )
        for key in ("vm_size", "os_sku"):
            value = node_pool.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"system_node_pool.{key} must be a non-empty string.")

        if node_pool.get("os_disk_type") not in {"Managed", "Ephemeral"}:
            errors.append(
                "system_node_pool.os_disk_type must be Managed or Ephemeral."
            )
        if not _is_integer(node_pool.get("node_count")) or node_pool["node_count"] < 2:
            errors.append("system_node_pool.node_count must be an integer of at least 2.")
        if (
            not _is_integer(node_pool.get("os_disk_size_gb"))
            or node_pool["os_disk_size_gb"] < 30
        ):
            errors.append(
                "system_node_pool.os_disk_size_gb must be an integer of at least 30."
            )
        if not _is_integer(node_pool.get("max_pods")) or node_pool["max_pods"] < 30:
            errors.append("system_node_pool.max_pods must be an integer of at least 30.")

    network_profile = configuration.get("network_profile")
    if not isinstance(network_profile, dict):
        errors.append("network_profile must be an object.")
    else:
        required_network_keys = {"pod_cidr", "service_cidr", "dns_service_ip"}
        for key in sorted(required_network_keys - network_profile.keys()):
            errors.append(f"network_profile is missing {key}.")

        networks: dict[str, ipaddress.IPv4Network | ipaddress.IPv6Network] = {}
        for key in ("pod_cidr", "service_cidr"):
            value = network_profile.get(key)
            try:
                networks[key] = ipaddress.ip_network(value, strict=True)
            except (TypeError, ValueError):
                errors.append(f"network_profile.{key} must be a valid CIDR range.")

        if len(networks) == 2 and networks["pod_cidr"].overlaps(
            networks["service_cidr"]
        ):
            errors.append("network_profile pod_cidr and service_cidr must not overlap.")

        dns_service_ip = network_profile.get("dns_service_ip")
        try:
            dns_address = ipaddress.ip_address(dns_service_ip)
        except (TypeError, ValueError):
            errors.append("network_profile.dns_service_ip must be a valid IP address.")
        else:
            service_network = networks.get("service_cidr")
            if service_network is not None and dns_address not in service_network:
                errors.append(
                    "network_profile.dns_service_ip must be inside service_cidr."
                )

    registry_name = configuration.get("container_registry_name")
    if not isinstance(registry_name, str) or not ACR_NAME_PATTERN.fullmatch(
        registry_name
    ):
        errors.append(
            "container_registry_name must contain 5-50 alphanumeric characters."
        )

    tags = configuration.get("tags")
    if not isinstance(tags, dict) or not tags:
        errors.append("tags must be a non-empty map of strings.")
    elif not all(isinstance(key, str) and isinstance(value, str) for key, value in tags.items()):
        errors.append("tags must contain only string keys and string values.")

    return errors


def summarize_plan(plan: dict[str, Any]) -> dict[str, list[str]]:
    summary: dict[str, list[str]] = {
        "create": [],
        "update": [],
        "replace": [],
        "delete": [],
        "other": [],
    }

    for resource_change in plan.get("resource_changes", []):
        address = resource_change.get("address", "<unknown>")
        actions = resource_change.get("change", {}).get("actions", [])
        if actions in (["no-op"], ["read"]):
            continue
        if actions == ["create"]:
            summary["create"].append(address)
        elif actions == ["update"]:
            summary["update"].append(address)
        elif actions in (["delete", "create"], ["create", "delete"]):
            summary["replace"].append(address)
        elif actions == ["delete"]:
            summary["delete"].append(address)
        else:
            summary["other"].append(f"{address}: {actions}")

    return summary


def print_plan_summary(summary: dict[str, list[str]]) -> None:
    print("\nInfrastructure comparison:")
    for action in ("create", "update", "replace", "delete", "other"):
        addresses = summary[action]
        print(f"  {action}: {len(addresses)}")
        for address in addresses:
            print(f"    - {address}")


def run_command(
    command: list[str],
    working_directory: Path,
    *,
    allowed_return_codes: set[int] | None = None,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    allowed = allowed_return_codes or {0}
    print(f"\n> {' '.join(command)}")
    result = subprocess.run(
        command,
        cwd=working_directory,
        check=False,
        capture_output=capture_output,
        text=True,
        encoding="utf-8",
    )
    if result.returncode not in allowed:
        if capture_output:
            if result.stdout:
                print(result.stdout, file=sys.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
        raise RuntimeError(
            f"{' '.join(command)} failed with exit code {result.returncode}."
        )
    return result


def parse_args(repo_root: Path) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate AKS tfvars, compare desired Terraform configuration with "
            "Azure, and optionally reconcile differences."
        )
    )
    parser.add_argument("--environment", default="aks-learning")
    parser.add_argument(
        "--var-file",
        type=Path,
        default=(
            repo_root
            / "components"
            / "azure-aks-cluster"
            / "terraform.tfvars"
        ),
        help=(
            "AKS tfvars path. Relative paths are resolved from the repository "
            "root."
        ),
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Run variable and Terraform validation without querying Azure state.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the saved plan when differences are detected.",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Skip the interactive apply confirmation. Requires --apply.",
    )
    parser.add_argument(
        "--allow-destructive",
        action="store_true",
        help="Allow a plan containing delete or replace actions. Requires --apply.",
    )
    args = parser.parse_args()

    if args.validate_only and args.apply:
        parser.error("--validate-only cannot be combined with --apply")
    if args.auto_approve and not args.apply:
        parser.error("--auto-approve requires --apply")
    if args.allow_destructive and not args.apply:
        parser.error("--allow-destructive requires --apply")

    return args


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    args = parse_args(repo_root)
    environment_path = repo_root / "environments" / args.environment
    module_path = repo_root / "components" / "azure-aks-cluster"
    var_file_path = (
        args.var_file
        if args.var_file.is_absolute()
        else repo_root / args.var_file
    )
    plan_path = environment_path / "aks-reconcile.tfplan"

    if shutil.which("terraform") is None:
        print("ERROR: terraform was not found in PATH.", file=sys.stderr)
        return 2
    if not environment_path.is_dir():
        print(f"ERROR: environment not found: {environment_path}", file=sys.stderr)
        return 2

    try:
        configuration = load_configuration(var_file_path)
    except FileNotFoundError:
        print(f"ERROR: variable file not found: {var_file_path}", file=sys.stderr)
        return 2
    except UnicodeDecodeError as error:
        print(f"ERROR: variable file must be UTF-8: {error}", file=sys.stderr)
        return 2
    except LarkError as error:
        print(f"ERROR: invalid HCL syntax in {var_file_path}: {error}", file=sys.stderr)
        return 2
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    errors = validate_configuration(
        configuration,
        expected_subscription_id=os.environ.get("ARM_SUBSCRIPTION_ID"),
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"AKS variable validation passed: {var_file_path}")

    try:
        run_command(["terraform", "fmt", "-check"], module_path)
        run_command(["terraform", "fmt", "-check"], environment_path)
        init_arguments = ["terraform", "init", "-input=false"]
        if args.validate_only:
            init_arguments.append("-backend=false")
        run_command(init_arguments, environment_path)
        run_command(["terraform", "validate", "-no-color"], environment_path)

        if args.validate_only:
            print("AKS Terraform validation passed.")
            return 0

        plan_result = run_command(
            [
                "terraform",
                "plan",
                "-input=false",
                "-no-color",
                "-detailed-exitcode",
                f"-var-file={var_file_path}",
                f"-out={plan_path}",
            ],
            environment_path,
            allowed_return_codes={0, 2},
        )
        if plan_result.returncode == 0:
            plan_path.unlink(missing_ok=True)
            print("Existing Azure infrastructure already matches Terraform.")
            return 0

        show_result = run_command(
            ["terraform", "show", "-json", str(plan_path)],
            environment_path,
            capture_output=True,
        )
        summary = summarize_plan(json.loads(show_result.stdout))
        print_plan_summary(summary)

        if not args.apply:
            print("\nDifferences detected. Re-run with --apply to reconcile them.")
            return 0

        destructive = bool(summary["replace"] or summary["delete"])
        if destructive and not args.allow_destructive:
            print(
                "ERROR: the plan contains delete or replace actions. Review it and "
                "re-run with --apply --allow-destructive only if intentional.",
                file=sys.stderr,
            )
            return 3

        if not args.auto_approve:
            try:
                confirmation = input("\nType 'apply' to reconcile this plan: ")
            except EOFError:
                confirmation = ""
            if confirmation != "apply":
                print("Apply cancelled; the saved plan was not executed.")
                return 4

        run_command(
            ["terraform", "apply", "-input=false", str(plan_path)],
            environment_path,
        )
        plan_path.unlink(missing_ok=True)
        print("AKS infrastructure reconciliation completed successfully.")
        return 0
    except (json.JSONDecodeError, OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
