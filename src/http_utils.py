"""Formatting utility functions."""

import humanize


def format_large_number(value: int) -> str:
    """Return a human-readable representation of a large number."""
    return humanize.intcomma(value)
# Trigger remediation demo
