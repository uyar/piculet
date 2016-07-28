from pytest import fixture, raises

from woody.wood import Rule, peck, scrape, xpath

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
    rule = Rule('name', path='./p1/n/text()', reducer='first')
    data = peck(people_root, rule)
    assert data == 'John Smith'


def test_peck_reducer_join_should_return_joined_text(people_root):
    rule = Rule('text', path='./p1//text()', reducer='join')
    data = peck(people_root, rule)
    assert data == 'John Smith42'


def test_peck_reducer_with_param_should_work(people_root):
    rule = Rule('text', path='.//n/text()', reducer='join?,')
    data = peck(people_root, rule)
    assert data == 'John Smith,Jane Doe'


def test_peck_unknown_reducer_should_raise_error(people_root):
    rule = Rule('text', path='./p1//text()', reducer='merge')
    with raises(ValueError):
        peck(people_root, rule)


def test_peck_non_matching_path_should_return_none(people_root):
    rule = Rule('name', path='./p3/a/text()', reducer='first')
    data = peck(people_root, rule)
    assert data is None


def test_scrape_no_prune_should_return_all(people_content):
    rules = [
        Rule('name', path='./p2/n/text()', reducer='first'),
        Rule('age', path='./p1/a/text()', reducer='first')
    ]
    data = scrape(people_content, rules)
    assert data == {'name': 'Jane Doe', 'age': '42'}


def test_scrape_prune_should_exclude_unselected_parts(people_content):
    rules = [
        Rule('name', path='.//n/text()', reducer='first'),
        Rule('age', path='.//a/text()', reducer='first')
    ]
    data = scrape(people_content, rules, prune='./p1')
    assert data == {'name': 'John Smith', 'age': '42'}


def test_scrape_missing_data_should_be_excluded(people_content):
    rules = [
        Rule('name', path='.//n/text()', reducer='first'),
        Rule('age', path='.//a/text()', reducer='first')
    ]
    data = scrape(people_content, rules, prune='./p2')
    assert data == {'name': 'Jane Doe'}


def test_scrape_prune_should_select_one_element(people_content):
    with raises(ValueError):
        scrape(people_content, rules=[], prune='.//n')


def test_scrape_no_rules_should_return_empty_result(people_content):
    data = scrape(people_content, rules=[])
    assert data == {}
