from __future__ import absolute_import, division, print_function, unicode_literals

from piculet import reducers


def test_reducer_first_should_return_first_item():
    assert reducers.first(['a', 'b', 'c']) == 'a'


def test_reducer_concat_should_return_concatenated_items():
    assert reducers.concat(['a', 'b', 'c']) == 'abc'


def test_reducer_clean_should_remove_extra_space():
    assert reducers.clean(['  a ', '   b', ' c ']) == 'a b c'


def test_reducer_clean_should_treat_nbsp_as_space():
    assert reducers.clean(['  a ', ' \xa0  b', ' c ']) == 'a b c'


def test_reducer_normalize_should_convert_to_lowercase():
    assert reducers.normalize(['A', 'B', 'C']) == 'abc'


def test_reducer_normalize_should_remove_nonalphanumeric_characters():
    assert reducers.normalize(['a+', '?b7', '{c}']) == 'ab7c'


def test_reducer_normalize_should_keep_underscores():
    assert reducers.normalize(['a_', 'b', 'c']) == 'a_bc'


def test_reducer_normalize_should_replace_spaces_with_underscores():
    assert reducers.normalize(['a', ' b', 'c']) == 'a_bc'
