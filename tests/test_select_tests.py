from scripts.select_tests import select_tests


def test_calculator_change_selects_calculator_tests():
    assert select_tests(["src/calculator.py"]) == [
        "tests/test_calculator.py"
    ]


def test_text_change_selects_text_tests():
    assert select_tests(["src/text_utils.py"]) == [
        "tests/test_text_utils.py"
    ]


def test_multiple_source_changes_select_multiple_tests():
    assert select_tests(
        ["src/calculator.py", "src/text_utils.py"]
    ) == [
        "tests/test_calculator.py",
        "tests/test_text_utils.py",
    ]


def test_documentation_change_skips_tests():
    assert select_tests(["README.md", "docs/guardrails.md"]) == []


def test_requirements_change_runs_full_suite():
    assert select_tests(["requirements.txt"]) == ["tests/"]


def test_unknown_source_change_runs_full_suite():
    assert select_tests(["src/new_module.py"]) == ["tests/"]
