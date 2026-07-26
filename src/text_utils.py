"""Small text-processing functions."""


def uppercase(value: str) -> str:
    """Convert text to uppercase."""
    return value.upper()


def lowercase(value: str) -> str:
    """Convert text to lowercase."""
    return value.lower()


def word_count(value: str) -> int:
    """Count whitespace-separated words."""
    return len(value.split())


def reverse_text(value: str) -> str:
    """Return text in reverse order."""
    return value[::-1]
