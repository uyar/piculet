from pytest import raises

from piculet import build_tree, extract, woodpecker, xpath


########################################
# xpath tests
########################################


generic_content = '<d><t1>foo</t1><t1 a="v"><t2>bar</t2></t1></d>'
generic_root = build_tree(generic_content)


def test_xpath_non_text_queries_should_return_nodes():
    selected = xpath(generic_root, './/t1')
    assert [s.tag for s in selected] == ['t1', 't1']


def test_xpath_child_text_queries_should_return_strings():
    selected = xpath(generic_root, './/t1/text()')
    assert selected == ['foo']


def test_xpath_descendant_text_queries_should_return_strings():
    selected = xpath(generic_root, './/t1//text()')
    assert selected == ['foo', 'bar']


def test_xpath_attr_queries_should_return_strings():
    selected = xpath(generic_root, './/t1/@a')
    assert selected == ['v']


########################################
# woodpecker tests
########################################


people_content = '<p><p1><n>John Smith</n><a>42</a></p1><p2><n>Jane Doe</n></p2></p>'
people_root = build_tree(people_content)


def test_peck_reducer_first_should_return_first_element():
    pecker = woodpecker(path='./p1/n/text()', reducer='first')
    data = pecker(people_root)
    assert data == 'John Smith'


def test_peck_reducer_join_should_return_joined_text():
    pecker = woodpecker(path='./p1//text()', reducer='join')
    data = pecker(people_root)
    assert data == 'John Smith42'


def test_peck_unknown_reducer_should_raise_error():
    with raises(ValueError):
        _ = woodpecker(path='./p1//text()', reducer='merge')


def test_peck_non_matching_path_should_return_none():
    pecker = woodpecker(path='./p3/a/text()', reducer='first')
    data = pecker(people_root)
    assert data is None


########################################
# extraction tests
########################################


def test_extract_no_subroot_should_return_all():
    rules = [
        {'key': 'name', 'value': {'path': './p2/n/text()', 'reducer': 'first'}},
        {'key': 'age', 'value': {'path': './p1/a/text()', 'reducer': 'first'}}
    ]
    data = extract(people_root, rules)
    assert data == {'name': 'Jane Doe', 'age': '42'}


def test_extract_subroot_should_exclude_unselected_parts():
    rules = [
        {'key': 'name', 'value': {'path': './/n/text()', 'reducer': 'first'}},
        {'key': 'age', 'value': {'path': './/a/text()', 'reducer': 'first'}}
    ]
    data = extract(people_root, rules, pre=[{'op': 'root', 'path': './p1'}])
    assert data == {'name': 'John Smith', 'age': '42'}


def test_extract_missing_data_should_be_excluded():
    rules = [
        {'key': 'name', 'value': {'path': './/n/text()', 'reducer': 'first'}},
        {'key': 'age', 'value': {'path': './/a/text()', 'reducer': 'first'}}
    ]
    data = extract(people_root, rules, pre=[{'op': 'root', 'path': './p2'}])
    assert data == {'name': 'Jane Doe'}


def test_extract_subroot_should_select_one_element():
    with raises(ValueError):
        _ = extract(people_root, items=[], pre=[{'op': 'root', 'path': './/n'}])


def test_extract_no_rules_should_return_empty_result():
    data = extract(people_root, items=[])
    assert data == {}
