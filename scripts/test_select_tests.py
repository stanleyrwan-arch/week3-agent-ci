def test_http_change_selects_http_tests():
    assert select_tests(["src/http_utils.py"]) == [
        "tests/test_http_utils.py"
    ]
