#!/usr/bin/env python3
"""
Remediation agent for one tightly scoped failure class:

    ModuleNotFoundError caused by a missing requirements.txt entry.

The agent may propose adding exactly one approved Python dependency.
It must not modify source code, tests, CI configuration, or deployment files.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import anthropic
from github import Github


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG = PROJECT_ROOT / "build_log.txt"
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"

# Blast-radius limit: only packages listed here may be added automatically.
APPROVED_DEPENDENCIES = {
    "humanize": "humanize",
}

SYSTEM_PROMPT = """
You are a narrowly scoped CI remediation agent.

Your only permitted task is to analyze a Python ModuleNotFoundError and
recommend adding one missing package to requirements.txt.

Rules:
1. Handle only ModuleNotFoundError.
2. Propose exactly one dependency.
3. Never modify source code, tests, workflows, infrastructure, secrets,
   deployment files, or environment variables.
4. Never remove or upgrade existing dependencies.
5. If the evidence is ambiguous, return safe_to_fix=false.
6. The proposed package must correspond directly to the missing import.
"""


def extract_missing_module(build_log: str) -> str | None:
    """Extract the missing import name from ModuleNotFoundError output."""
    pattern = r"ModuleNotFoundError:\s+No module named ['\"]([^'\"]+)['\"]"
    match = re.search(pattern, build_log)
    if not match:
        return None

    # For imports such as package.submodule, dependency is normally top-level.
    return match.group(1).split(".")[0]


def read_requirements() -> list[str]:
    """Read non-empty requirements.txt lines."""
    if not REQUIREMENTS_PATH.exists():
        return []

    return [
        line.strip()
        for line in REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def analyze_with_agent(build_log: str, missing_module: str) -> dict:
    """Ask Claude to classify the failure using a constrained JSON schema."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    schema = {
        "type": "object",
        "properties": {
            "failure_class": {"type": "string"},
            "missing_module": {"type": "string"},
            "recommended_package": {"type": "string"},
            "root_cause": {"type": "string"},
            "fix_description": {"type": "string"},
            "safe_to_fix": {"type": "boolean"},
        },
        "required": [
            "failure_class",
            "missing_module",
            "recommended_package",
            "root_cause",
            "fix_description",
            "safe_to_fix",
        ],
        "additionalProperties": False,
    }

    response = client.messages.create(
        model=os.environ.get("MODEL", "claude-haiku-4-5"),
        max_tokens=700,
        system=SYSTEM_PROMPT,
        output_config={
            "format": {
                "type": "json_schema",
                "schema": schema,
            }
        },
        messages=[
            {
                "role": "user",
                "content": (
                    f"Detected missing module: {missing_module}\n\n"
                    f"Build log:\n```\n{build_log}\n```"
                ),
            }
        ],
    )

    text = next(block.text for block in response.content if block.type == "text")
    return json.loads(text)


def validate_proposal(proposal: dict, missing_module: str) -> str:
    """
    Apply deterministic guardrails after the LLM response.

    Returns the approved dependency name or raises ValueError.
    """
    if proposal.get("safe_to_fix") is not True:
        raise ValueError("Agent marked this failure unsafe to remediate.")

    if proposal.get("failure_class") != "ModuleNotFoundError":
        raise ValueError("Agent returned an unsupported failure class.")

    if proposal.get("missing_module") != missing_module:
        raise ValueError("Agent missing-module result does not match the log.")

    approved_package = APPROVED_DEPENDENCIES.get(missing_module)
    if not approved_package:
        raise ValueError(
            f"Missing module '{missing_module}' is not in the approved allowlist."
        )

    if proposal.get("recommended_package") != approved_package:
        raise ValueError("Agent package recommendation failed allowlist validation.")

    return approved_package


def build_updated_requirements(package: str) -> str:
    """Return requirements.txt content with one missing dependency appended."""
    requirements = read_requirements()

    normalized_names = {
        re.split(r"[<>=!~\[]", line, maxsplit=1)[0].strip().lower()
        for line in requirements
    }

    if package.lower() not in normalized_names:
        requirements.append(package)

    return "\n".join(requirements) + "\n"


def open_pull_request(
    updated_content: str,
    proposal: dict,
    base_branch: str,
) -> str:
    """Create a branch, update requirements.txt, and open a human-reviewed PR."""
    github = Github(os.environ["GH_TOKEN"])
    repo = github.get_repo(os.environ["REPO"])

    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    branch_name = f"bot/fix-missing-dependency-{run_id}"

    base_ref = repo.get_git_ref(f"heads/{base_branch}")
    repo.create_git_ref(
        ref=f"refs/heads/{branch_name}",
        sha=base_ref.object.sha,
    )

    remote_requirements = repo.get_contents(
        "requirements.txt",
        ref=base_branch,
    )

    repo.update_file(
        path="requirements.txt",
        message="[bot] fix: add missing Python dependency",
        content=updated_content,
        sha=remote_requirements.sha,
        branch=branch_name,
    )

    pr = repo.create_pull(
        title="[Bot Fix] Add missing dependency",
        body=(
            "## Agent-Proposed Remediation\n\n"
            f"**Root cause:** {proposal['root_cause']}\n\n"
            f"**Fix:** {proposal['fix_description']}\n\n"
            "### Guardrails\n"
            "- Only `requirements.txt` was changed.\n"
            "- The package passed a deterministic allowlist check.\n"
            "- Source code, tests, workflows, and deployment files were not changed.\n"
            "- This PR requires human review and is not automatically merged.\n"
        ),
        head=branch_name,
        base=base_branch,
    )

    return pr.html_url


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default=str(DEFAULT_LOG))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--open-pr", action="store_true")
    args = parser.parse_args()

    build_log = Path(args.log).read_text(encoding="utf-8")
    missing_module = extract_missing_module(build_log)

    if not missing_module:
        print("Unsupported failure: no ModuleNotFoundError was found.")
        return 2

    proposal = analyze_with_agent(build_log, missing_module)
    package = validate_proposal(proposal, missing_module)
    updated_requirements = build_updated_requirements(package)

    print(f"Failure class: {proposal['failure_class']}")
    print(f"Root cause:    {proposal['root_cause']}")
    print(f"Fix:           {proposal['fix_description']}")
    print(f"Package:       {package}")
    print("\n--- proposed requirements.txt ---")
    print(updated_requirements, end="")

    if args.open_pr:
        base_branch = os.environ.get("BASE_BRANCH", "main")
        url = open_pull_request(updated_requirements, proposal, base_branch)
        print(f"\nOpened PR: {url}")
    else:
        print("\nDry run only; no repository files were changed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
