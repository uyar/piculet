from piculet import build_tree, xpath


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


def test_non_absolute_queries_should_be_ok():
    selected = xpath("//t1")(root)
    assert [s.tag for s in selected] == ["t1", "t1"]
