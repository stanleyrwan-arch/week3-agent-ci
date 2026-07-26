import pytest

from scripts.remediation_agent import (
    build_updated_requirements,
    extract_missing_module,
    validate_proposal,
)


def test_extract_missing_module():
    log = "ModuleNotFoundError: No module named 'humanize'"
    assert extract_missing_module(log) == "humanize"


def test_extract_top_level_module():
    log = "ModuleNotFoundError: No module named 'humanize.filesize'"
    assert extract_missing_module(log) == "humanize"


def test_non_matching_failure_returns_none():
    assert extract_missing_module("AssertionError: 1 != 2") is None


def test_valid_proposal_passes_allowlist():
    proposal = {
        "safe_to_fix": True,
        "failure_class": "ModuleNotFoundError",
        "missing_module": "humanize",
        "recommended_package": "humanize",
    }

    assert validate_proposal(proposal, "humanize") == "humanize"


def test_unapproved_dependency_is_rejected():
    proposal = {
        "safe_to_fix": True,
        "failure_class": "ModuleNotFoundError",
        "missing_module": "unknown_package",
        "recommended_package": "unknown_package",
    }

    with pytest.raises(ValueError):
        validate_proposal(proposal, "unknown_package")


def test_agent_cannot_change_package_name():
    proposal = {
        "safe_to_fix": True,
        "failure_class": "ModuleNotFoundError",
        "missing_module": "humanize",
        "recommended_package": "different-package",
    }

    with pytest.raises(ValueError):
        validate_proposal(proposal, "humanize")
