from shortener.codes import ALPHABET, CODE_LENGTH, generate_code


def test_code_has_the_configured_length() -> None:
    assert len(generate_code()) == CODE_LENGTH


def test_code_uses_only_alphabet_characters() -> None:
    assert set(generate_code()) <= set(ALPHABET)


def test_codes_do_not_repeat_across_many_draws() -> None:
    codes = {generate_code() for _ in range(1000)}
    assert len(codes) == 1000
