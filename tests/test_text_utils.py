from src.text_utils import lowercase, reverse_text, uppercase, word_count


def test_uppercase():
    assert uppercase("hello") == "HELLO"


def test_lowercase():
    assert lowercase("HELLO") == "hello"


def test_word_count():
    assert word_count("one two three") == 3


def test_reverse_text():
    assert reverse_text("abc") == "cba"
