from __future__ import absolute_import, division, print_function, unicode_literals

from pytest import fixture, raises

import os

from piculet import build_tree, extract, reducers


shining_file = os.path.join(os.path.dirname(__file__), '..', 'examples', 'shining.html')
shining_content = open(shining_file).read()


@fixture
def shining():
    """Root node of the XML tree for the movie document "The Shining"."""
    return build_tree(shining_content)


def test_preprocess_unknown_operation_should_raise_error(shining):
    with raises(ValueError):
        extract(shining, [], pre=[{"op": "foo"}])


def test_preprocess_root_multiple_should_raise_error(shining):
    with raises(ValueError):
        extract(shining, [], pre=[{"op": "root", "path": ".//div"}])


def test_preprocess_root_none_should_return_empty_result(shining):
    items = [{"key": "title", "value": {"path": ".//title/text()", "reduce": reducers.first}}]
    data = extract(shining, items, pre=[{"op": "root", "path": ".//foo"}])
    assert data == {}


def test_preprocess_root_should_exclude_unselected_parts(shining):
    items = [{"key": "foo", "value": {"path": ".//h3/text()", "reduce": reducers.first}}]
    data = extract(shining, items, pre=[{"op": "root", "path": ".//div[@class='director']"}])
    assert data == {'foo': 'Director:'}


def test_preprocess_remove_should_remove_selected_node(shining):
    items = [{"key": "cast",
              "value": {
                  "foreach": ".//table[@class='cast']/tr",
                  "items": [
                      {"key": "name",
                       "value": {"path": "./td[1]/a/text()",
                                 "reduce": reducers.first}}
                  ]
              }}]
    data = extract(shining, items, pre=[{"op": "remove", "path": ".//tr[1]"}])
    assert data == {'cast': [{'name': 'Shelley Duvall'}]}


def test_preprocess_remove_selected_none_should_not_cause_error(shining):
    items = [{"key": "cast",
              "value": {
                  "foreach": ".//table[@class='cast']/tr",
                  "items": [
                      {"key": "name",
                       "value": {"path": "./td[1]/a/text()",
                                 "reduce": reducers.first}}
                  ]
              }}]
    data = extract(shining, items, pre=[{"op": "remove", "path": ".//tr[50]"}])
    assert data == {'cast': [{'name': 'Jack Nicholson'}, {'name': 'Shelley Duvall'}]}
