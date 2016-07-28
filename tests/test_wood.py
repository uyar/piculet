from pytest import fixture

from woody.wood import Reducer, Rule, peck, xpath

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
def person_content():
    """XML content to represent the data of a person."""
    return '<p><n>John Smith</n><a>42</a><b></b><b></b></p>'


@fixture(scope='session')
def person_root(person_content):
    """XML document to represent the data of a person."""
    return ElementTree.fromstring(person_content)


def test_peck_non_matching_path_should_return_none(person_root):
    rule = Rule('name', path='.//z/text()', reducer=Reducer.join)
    data = peck(person_root, rule)
    assert data is None


def test_peck_reducer_first_should_return_first_element(person_root):
    rule = Rule('name', path='.//n/text()', reducer=Reducer.first)
    data = peck(person_root, rule)
    assert data == 'John Smith'


def test_peck_reducer_join_should_return_joined_text(person_root):
    rule = Rule('text', path='.//text()', reducer=Reducer.join)
    data = peck(person_root, rule)
    assert data == 'John Smith42'
