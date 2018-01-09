from __future__ import absolute_import, division, print_function, unicode_literals

from piculet import build_tree, xpath


generic_content = '<d><t1>foo</t1><t1 a="v"><t2>bar</t2></t1></d>'
generic_root = build_tree(generic_content)


def test_xpath_non_text_queries_should_return_nodes():
    selected = xpath(generic_root, ".//t1")
    assert [s.tag for s in selected] == ['t1', 't1']


def test_xpath_child_text_queries_should_return_strings():
    selected = xpath(generic_root, ".//t1/text()")
    assert selected == ['foo']


def test_xpath_descendant_text_queries_should_return_strings():
    selected = xpath(generic_root, ".//t1//text()")
    assert selected == ['foo', 'bar']


def test_xpath_attr_queries_should_return_strings():
    selected = xpath(generic_root, ".//t1/@a")
    assert selected == ['v']
