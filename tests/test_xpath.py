from __future__ import absolute_import, division, print_function, unicode_literals

from piculet import build_tree, xpath


content = '<d><t1>foo</t1><t1 a="v"><t2>bar</t2></t1></d>'
root = build_tree(content)


def test_non_text_queries_should_return_elements():
    selected = xpath(root, './/t1')
    assert [s.tag for s in selected] == ['t1', 't1']


def test_child_text_queries_should_return_strings():
    selected = xpath(root, './/t1/text()')
    assert selected == ['foo']


def test_descendant_text_queries_should_return_strings():
    selected = xpath(root, './/t1//text()')
    assert selected == ['foo', 'bar']


def test_attr_queries_should_return_strings():
    selected = xpath(root, './/t1/@a')
    assert selected == ['v']


def test_non_absolute_queries_should_be_ok():
    selected = xpath(root, '//t1')
    assert [s.tag for s in selected] == ['t1', 't1']
