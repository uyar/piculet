from piculet import build_tree, get_parent, get_root, xpath


content = '<d><t1>foo</t1><t1 a="v"><t2>bar</t2></t1></d>'
root = build_tree(content)


def test_build_tree_should_return_root():
    assert root.tag == "d"


def test_get_root_should_return_root():
    element = xpath("//t2")(root)[0]
    assert get_root(element) is root


def test_get_root_should_return_root_for_root():
    assert get_root(root) is root


def test_get_parent_should_return_parent():
    element = xpath("//t2")(root)[0]
    assert get_parent(element).tag == "t1"


def test_get_parent_should_return_none_for_root():
    assert get_parent(root) is None
