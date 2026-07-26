"""Basic calculator functions."""


def add(a: float, b: float) -> float:
    """Return the sum of two values."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Return the difference between two values."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Return the product of two values."""
    return a * b


def divide(a: float, b: float) -> float:
    """Return a divided by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
