from pytest import fixture

from woody.wood import xpath

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
