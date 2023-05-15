from pytest import mark, raises

from piculet import _LXML_AVAILABLE, build_tree, xpath


content = '<d><t1>foo</t1><t1 a="v"><t2>bar</t2></t1></d>'
root = build_tree(content)


def test_non_text_queries_should_return_elements():
    selected = xpath(".//t1")(root)
    assert [s.tag for s in selected] == ["t1", "t1"]


def test_child_text_queries_should_return_strings():
    selected = xpath(".//t1/text()")(root)
    assert selected == ["foo"]


def test_descendant_text_queries_should_return_strings():
    selected = xpath(".//t1//text()")(root)
    assert selected == ["foo", "bar"]


def test_attr_queries_should_return_strings():
    selected = xpath(".//t1/@a")(root)
    assert selected == ["v"]


def test_absolute_queries_should_be_ok():
    selected = xpath("//t1")(root)
    assert [s.tag for s in selected] == ["t1", "t1"]


def test_absolute_queries_on_subelements_should_be_ok():
    element = xpath("//t2")(root)[0]
    selected = xpath("//t1")(element)
    assert [s.tag for s in selected] == ["t1", "t1"]


def test_queries_starting_with_parent_should_be_ok():
    element = xpath("//t2")(root)[0]
    selected = xpath("../@a")(element)
    assert selected == ["v"]


def test_queries_starting_with_multiple_parents_should_be_ok():
    element = xpath("//t2")(root)[0]
    selected = xpath("../../t1")(element)
    assert [s.tag for s in selected] == ["t1", "t1"]


def test_queries_starting_with_parent_from_root_should_be_ok():
    selected = xpath("../a")(root)
    assert selected == []


def test_queries_climbing_above_root_should_be_ok():
    element = xpath("//t2")(root)[0]
    selected = xpath("../../../../../../a")(element)
    assert selected == []


def test_child_text_queries_starting_with_parent_from_root_should_be_ok():
    selected = xpath("../a/text()")(root)
    assert selected == []


def test_descendant_text_queries_starting_with_parent_from_root_should_be_ok():
    selected = xpath("..//a/text()")(root)
    assert selected == []


def test_attribute_queries_starting_with_parent_from_root_should_be_ok():
    selected = xpath("../@a")(root)
    assert selected == []


@mark.skipif(_LXML_AVAILABLE, reason="starts-with function is supported in lxml")
def test_lxml_should_be_used_if_available():
    with raises(SyntaxError):
        xpath(".//t1[starts-with(text(), 'f')]")(root)
