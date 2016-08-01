from pytest import fixture, raises

from woody.wood import WoodPecker, extract, xpath

from xml.etree import ElementTree


@fixture(scope='session')
def generic_xml():
    """Simple XML document with generic content."""
    content = '<d><t1>foo</t1><t1 a="v"><t2>bar</t2></t1></d>'
    return ElementTree.fromstring(content)


def test_xpath_non_text_queries_should_return_nodes(generic_xml):
    selected = xpath(generic_xml, './/t1')
    assert [s.tag for s in selected] == ['t1', 't1']


def test_xpath_child_text_queries_should_return_strings(generic_xml):
    selected = xpath(generic_xml, './/t1/text()')
    assert selected == ['foo']


def test_xpath_descendant_text_queries_should_return_strings(generic_xml):
    selected = xpath(generic_xml, './/t1//text()')
    assert selected == ['foo', 'bar']


def test_xpath_attr_queries_should_return_strings(generic_xml):
    selected = xpath(generic_xml, './/t1/@a')
    assert selected == ['v']


@fixture(scope='session')
def people_content():
    """XML content to represent the data of multiple persons."""
    return '<p><p1><n>John Smith</n><a>42</a></p1><p2><n>Jane Doe</n></p2></p>'


@fixture(scope='session')
def people_root(people_content):
    """XML document to represent the data of a person."""
    return ElementTree.fromstring(people_content)


def test_peck_reducer_first_should_return_first_element(people_root):
    pecker = WoodPecker('name', path='./p1/n/text()', reducer='first')
    data = pecker.peck(people_root)
    assert data == 'John Smith'


def test_peck_reducer_join_should_return_joined_text(people_root):
    pecker = WoodPecker('text', path='./p1//text()', reducer='join')
    data = pecker.peck(people_root)
    assert data == 'John Smith42'


def test_peck_unknown_reducer_should_raise_error(people_root):
    with raises(ValueError):
        WoodPecker('text', path='./p1//text()', reducer='merge')


def test_peck_non_matching_path_should_return_none(people_root):
    pecker = WoodPecker('name', path='./p3/a/text()', reducer='first')
    data = pecker.peck(people_root)
    assert data is None


def test_scrape_no_prune_should_return_all(people_content):
    rules = [
        {'key': 'name', 'path': './p2/n/text()', 'reducer': 'first'},
        {'key': 'age', 'path': './p1/a/text()', 'reducer': 'first'}
    ]
    data = extract(people_content, rules)
    assert data == {'name': 'Jane Doe', 'age': '42'}


def test_scrape_prune_should_exclude_unselected_parts(people_content):
    rules = [
        {'key': 'name', 'path': './/n/text()', 'reducer': 'first'},
        {'key': 'age', 'path': './/a/text()', 'reducer': 'first'}
    ]
    data = extract(people_content, rules, prune='./p1')
    assert data == {'name': 'John Smith', 'age': '42'}


def test_scrape_missing_data_should_be_excluded(people_content):
    rules = [
        {'key': 'name', 'path': './/n/text()', 'reducer': 'first'},
        {'key': 'age', 'path': './/a/text()', 'reducer': 'first'}
    ]
    data = extract(people_content, rules, prune='./p2')
    assert data == {'name': 'Jane Doe'}


def test_scrape_prune_should_select_one_element(people_content):
    with raises(ValueError):
        extract(people_content, rules=[], prune='.//n')


def test_scrape_no_rules_should_return_empty_result(people_content):
    data = extract(people_content, rules=[])
    assert data == {}
