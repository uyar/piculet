from pytest import fixture, mark, raises

import os
import time

from woody import ElementTree
from woody import _get_document, extract, scrape, woodpecker, xpath


@fixture(scope='module')
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


@fixture(scope='module')
def people_root():
    """XML document to represent the data of a person."""
    content = '<p><p1><n>John Smith</n><a>42</a></p1><p2><n>Jane Doe</n></p2></p>'
    return ElementTree.fromstring(content)


def test_peck_reducer_first_should_return_first_element(people_root):
    pecker = woodpecker(path='./p1/n/text()', reducer='first')
    data = pecker(people_root)
    assert data == 'John Smith'


def test_peck_reducer_join_should_return_joined_text(people_root):
    pecker = woodpecker(path='./p1//text()', reducer='join')
    data = pecker(people_root)
    assert data == 'John Smith42'


def test_peck_unknown_reducer_should_raise_error(people_root):
    with raises(ValueError):
        woodpecker(path='./p1//text()', reducer='merge')


def test_peck_non_matching_path_should_return_none(people_root):
    pecker = woodpecker(path='./p3/a/text()', reducer='first')
    data = pecker(people_root)
    assert data is None


def test_scrape_no_subroot_should_return_all(people_root):
    rules = [
        {'key': 'name', 'value': {'path': './p2/n/text()', 'reducer': 'first'}},
        {'key': 'age', 'value': {'path': './p1/a/text()', 'reducer': 'first'}}
    ]
    data = extract(people_root, rules)
    assert data == {'name': 'Jane Doe', 'age': '42'}


def test_scrape_subroot_should_exclude_unselected_parts(people_root):
    rules = [
        {'key': 'name', 'value': {'path': './/n/text()', 'reducer': 'first'}},
        {'key': 'age', 'value': {'path': './/a/text()', 'reducer': 'first'}}
    ]
    data = extract(people_root, rules, pre=[{'op': 'root', 'path': './p1'}])
    assert data == {'name': 'John Smith', 'age': '42'}


def test_scrape_missing_data_should_be_excluded(people_root):
    rules = [
        {'key': 'name', 'value': {'path': './/n/text()', 'reducer': 'first'}},
        {'key': 'age', 'value': {'path': './/a/text()', 'reducer': 'first'}}
    ]
    data = extract(people_root, rules, pre=[{'op': 'root', 'path': './p2'}])
    assert data == {'name': 'Jane Doe'}


def test_scrape_subroot_should_select_one_element(people_root):
    with raises(ValueError):
        extract(people_root, items=[], pre=[{'op': 'root', 'path': './/n'}])


def test_scrape_no_rules_should_return_empty_result(people_root):
    data = extract(people_root, items=[])
    assert data == {}


TEST_SITE = 'http://en.wikipedia.org'


@fixture(scope='module')
def dummy_spec():
    """Dummy data extraction spec."""
    return {
        "base_url": TEST_SITE,
        "scrapers": [
            {
                "id": "dummy",
                "url": "/",
                "items": []
            }
        ]
    }


@fixture(scope='module', autouse=True)
def get_test_page(dummy_spec):
    """Store the test page in the cache."""
    for scraper in dummy_spec['scrapers']:
        url = dummy_spec['base_url'] + scraper['url']
        _get_document(url)


@mark.skip
def test_scrape_url_uncached_should_retrieve_from_web(dummy_spec):
    del os.environ['WOODY_WEB_CACHE']
    start = time.time()
    scrape(dummy_spec, 'dummy')
    end = time.time()
    assert end - start > 1


def test_scrape_url_cached_should_read_from_disk(dummy_spec):
    start = time.time()
    scrape(dummy_spec, 'dummy')
    end = time.time()
    assert end - start < 1


def test_scrape_url_multiple_ids_should_raise_error(dummy_spec):
    scrapers = dummy_spec['scrapers']
    scrapers.append(scrapers[0])
    with raises(ValueError):
        scrape(dummy_spec, 'dummy')
