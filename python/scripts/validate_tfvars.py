from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import hcl2
from hcl2 import SerializationOptions
from lark.exceptions import LarkError

ALLOWED_GROUPS = {"cloud_admin", "developers", "readers", "aks_admins"}
USERNAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
DOMAIN_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)"
    r"(?:\.(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?))*$"
)
UPN_PATTERN = re.compile(r"^[^@\s]+@([^@\s]+)$")
SUBSCRIPTION_SCOPE_PATTERN = re.compile(
    r"^/subscriptions/[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}"
    r"[0-9a-fA-F]{12}(?:/.*)?$"
)
MANAGEMENT_GROUP_SCOPE_PATTERN = re.compile(
    r"^/providers/Microsoft\.Management/managementGroups/[^/]+(?:/.*)?$",
    re.IGNORECASE,
)


def is_valid_upn(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    match = UPN_PATTERN.fullmatch(value)
    return match is not None and bool(DOMAIN_PATTERN.fullmatch(match.group(1)))


def validate_configuration(configuration: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    upn_suffix = configuration.get("upn_suffix", "trackmyop.in")
    if not isinstance(upn_suffix, str) or not DOMAIN_PATTERN.fullmatch(upn_suffix):
        errors.append("upn_suffix must be a domain name without '@'.")
        upn_suffix = ""

    users = configuration.get("users", {})
    if not isinstance(users, dict):
        errors.append("users must be a map from usernames to lists of groups.")
        users = {}

    normalized_users: set[str] = set()
    for username, groups in users.items():
        if not isinstance(username, str) or not USERNAME_PATTERN.fullmatch(username):
            errors.append(f"users key {username!r} must be a lowercase username.")
            continue
        normalized_users.add(username)
        if not isinstance(groups, list) or not groups:
            errors.append(f"users.{username} must contain at least one group.")
            continue
        if all(isinstance(group, str) for group in groups):
            if len(groups) != len(set(groups)):
                errors.append(f"users.{username} contains duplicate group names.")
        for group in groups:
            if not isinstance(group, str) or group not in ALLOWED_GROUPS:
                errors.append(
                    f"users.{username} has unsupported group {group!r}; "
                    f"choose from {', '.join(sorted(ALLOWED_GROUPS))}."
                )

    upn_overrides = configuration.get("user_principal_names", {})
    if not isinstance(upn_overrides, dict):
        errors.append("user_principal_names must be a map of usernames to UPNs.")
        upn_overrides = {}

    for username, upn in upn_overrides.items():
        if username not in normalized_users:
            errors.append(
                f"user_principal_names.{username} does not have a matching users entry."
            )
        if not is_valid_upn(upn):
            errors.append(f"user_principal_names.{username} must be a valid UPN.")

    resolved_upns: dict[str, str] = {}
    for username in normalized_users:
        upn = upn_overrides.get(username, f"{username}@{upn_suffix}")
        if is_valid_upn(upn):
            normalized_upn = upn.casefold()
            if normalized_upn in resolved_upns:
                errors.append(
                    f"users {resolved_upns[normalized_upn]!r} and {username!r} "
                    f"resolve to the same UPN {upn!r}."
                )
            else:
                resolved_upns[normalized_upn] = username

    assignments = configuration.get("rbac_assignments", {})
    if not isinstance(assignments, dict):
        errors.append("rbac_assignments must be a map.")
        assignments = {}

    for assignment_name, assignment in assignments.items():
        if not isinstance(assignment, dict):
            errors.append(f"rbac_assignments.{assignment_name} must be an object.")
            continue

        group = assignment.get("group")
        role = assignment.get("role_definition_name")
        scope = assignment.get("scope")

        if not isinstance(group, str) or group not in ALLOWED_GROUPS:
            errors.append(
                f"rbac_assignments.{assignment_name}.group must be one of "
                f"{', '.join(sorted(ALLOWED_GROUPS))}."
            )
        if not isinstance(role, str) or not role.strip():
            errors.append(
                f"rbac_assignments.{assignment_name}.role_definition_name must not be empty."
            )
        if (
            not isinstance(scope, str)
            or "<" in scope
            or ">" in scope
            or not (
                SUBSCRIPTION_SCOPE_PATTERN.fullmatch(scope)
                or MANAGEMENT_GROUP_SCOPE_PATTERN.fullmatch(scope)
            )
        ):
            errors.append(
                f"rbac_assignments.{assignment_name}.scope must be a full Azure "
                "subscription or management-group resource ID without placeholders."
            )

    return errors


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


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Validate Terraform identity variables before running Terraform."
    )
    parser.add_argument(
        "--var-file",
        type=Path,
        default=repo_root / "components" / "identity" / "terraform.tfvars",
        help="Path to the Terraform .tfvars file.",
    )
    args = parser.parse_args()

    try:
        configuration = load_configuration(args.var_file)
    except FileNotFoundError:
        print(f"ERROR: variable file not found: {args.var_file}", file=sys.stderr)
        return 2
    except UnicodeDecodeError as error:
        print(f"ERROR: variable file must be UTF-8: {error}", file=sys.stderr)
        return 2
    except LarkError as error:
        print(f"ERROR: invalid HCL syntax in {args.var_file}: {error}", file=sys.stderr)
        return 2
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    errors = validate_configuration(configuration)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        "Terraform variable validation passed: "
        f"{len(configuration.get('users', {}))} user(s), "
        f"{len(configuration.get('rbac_assignments', {}))} RBAC assignment(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
