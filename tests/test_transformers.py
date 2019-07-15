from piculet import transformers


def test_transformer_clean_should_remove_extra_space():
    assert transformers.clean("  a    b c ") == "a b c"


def test_transformer_clean_should_treat_nbsp_as_space():
    assert transformers.clean("  a  \xa0  b c ") == "a b c"


def test_transformer_normalize_should_convert_to_lowercase():
    assert transformers.normalize("ABC") == "abc"


def test_transformer_normalize_should_remove_nonalphanumeric_characters():
    assert transformers.normalize("a+?b7{c}") == "ab7c"


def test_transformer_normalize_should_keep_underscores():
    assert transformers.normalize("a_bc") == "a_bc"


def test_transformer_normalize_should_replace_spaces_with_underscores():
    assert transformers.normalize("a bc") == "a_bc"
