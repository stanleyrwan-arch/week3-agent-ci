from src.http_utils import format_large_number


def test_format_large_number():
    assert format_large_number(1000) == "1,000"


def test_format_larger_number():
    assert format_large_number(1000000) == "1,000,000"
