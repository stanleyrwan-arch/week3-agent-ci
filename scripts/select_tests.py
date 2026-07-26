#!/usr/bin/env python3
"""
Select tests based on changed files.

Rules:
- src/calculator.py -> tests/test_calculator.py
- src/text_utils.py -> tests/test_text_utils.py
- test file changed -> run that test file
- shared Python/config files -> run the full test suite
- docs/README-only changes -> skip tests
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TEST_MAPPING = {
    "src/calculator.py": "tests/test_calculator.py",
    "src/text_utils.py": "tests/test_text_utils.py",
    "src/http_utils.py": "tests/test_http_utils.py",
}


FULL_SUITE_TRIGGERS = {
    "requirements.txt",
    "pyproject.toml",
    "pytest.ini",
    "setup.py",
    "setup.cfg",
}

DOC_PREFIXES = (
    "docs/",
    ".github/",
)

DOC_FILES = {
    "README.md",
}


def get_changed_files(base_ref: str, head_ref: str) -> list[str]:
    """Return files changed between two Git references."""
    result = subprocess.run(
        ["git", "diff", "--name-only", base_ref, head_ref],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def select_tests(changed_files: list[str]) -> list[str]:
    """Map changed files to the minimum relevant test set."""
    selected: set[str] = set()

    for file_path in changed_files:
        if file_path in FULL_SUITE_TRIGGERS:
            return ["tests/"]

        if file_path in TEST_MAPPING:
            selected.add(TEST_MAPPING[file_path])
            continue

        if file_path.startswith("tests/") and file_path.endswith(".py"):
            selected.add(file_path)
            continue

        if file_path.startswith("src/") and file_path.endswith(".py"):
            # Unknown source module: safely fall back to the full suite.
            return ["tests/"]

        if file_path in DOC_FILES or file_path.startswith(DOC_PREFIXES):
            continue

        # Unknown non-document change: prefer safety over skipping.
        return ["tests/"]

    return sorted(selected)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="Base Git reference")
    parser.add_argument("--head", required=True, help="Head Git reference")
    args = parser.parse_args()

    changed_files = get_changed_files(args.base, args.head)
    selected_tests = select_tests(changed_files)

    print("Changed files:")
    for file_path in changed_files:
        print(f"  - {file_path}")

    if not selected_tests:
        print("TEST_MODE=skip")
        print("SELECTED_TESTS=")
        print("No relevant code changes; tests may be skipped.")
        return 0

    print("TEST_MODE=selected")
    print(f"SELECTED_TESTS={' '.join(selected_tests)}")
    print(f"Selected {len(selected_tests)} test target(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
