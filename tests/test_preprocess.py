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


def test_preprocess_set_attr_value_from_str_should_set_attribute_for_selected_nodes(shining):
    items = [{"key": "genres",
              "value": {
                  "foreach": ".//li[@foo='bar']",
                  "path": "./text()",
                  "reduce": reducers.first
              }}]
    data = extract(shining, items,
                   pre=[{"op": "set_attr", "path": ".//ul[@class='genres']/li",
                         "name": "foo", "value": "bar"}])
    assert data == {'genres': ['Horror', 'Drama']}


def test_preprocess_set_attr_value_from_path_should_set_attribute_for_selected_nodes(shining):
    items = [{"key": "genres",
              "value": {
                  "foreach": ".//li[@foo]",
                  "path": "./@foo",
                  "reduce": reducers.first
              }}]
    data = extract(shining, items,
                   pre=[{"op": "set_attr", "path": ".//ul[@class='genres']/li",
                         "name": "foo",
                         "value": {"path": "./text()", "reduce": reducers.first}}])
    assert data == {'genres': ['Horror', 'Drama']}


def test_preprocess_set_attr_value_from_path_no_value_should_raise_error(shining):
    items = [{"key": "genres",
              "value": {
                  "foreach": ".//li[@foo]",
                  "path": "./@foo",
                  "reduce": reducers.first
              }}]
    with raises(ValueError):
        extract(shining, items,
                pre=[{"op": "set_attr", "path": ".//ul[@class='genres']/li",
                      "name": "foo",
                      "value": {"path": "./@bar", "reduce": reducers.first}}])


def test_preprocess_set_attr_name_from_path_should_set_attribute_for_selected_nodes(shining):
    items = [{"key": "genres",
              "value": {
                  "foreach": ".//li[@Horror]",
                  "path": "./@Horror",
                  "reduce": reducers.first
              }}]
    data = extract(shining, items,
                   pre=[{"op": "set_attr", "path": ".//ul[@class='genres']/li",
                         "name": {"path": "./text()", "reduce": reducers.first},
                         "value": "bar"}])
    assert data == {'genres': ['bar']}


def test_preprocess_set_attr_name_from_path_no_value_should_raise_error(shining):
    items = [{"key": "genres",
              "value": {
                  "foreach": ".//li[@Horror]",
                  "path": "./@Horror",
                  "reduce": reducers.first
              }}]
    with raises(ValueError):
        extract(shining, items,
                pre=[{"op": "set_attr", "path": ".//ul[@class='genres']/li",
                      "name": {"path": "./@bar", "reduce": reducers.first},
                      "value": "bar"}])


def test_preprocess_set_attr_selected_none_should_not_cause_error(shining):
    items = [{"key": "genres",
              "value": {
                  "foreach": ".//li[@foo='bar']",
                  "path": "./@foo",
                  "reduce": reducers.first
              }}]
    data = extract(shining, items,
                   pre=[{"op": "set_attr", "path": ".//foo", "name": "foo", "value": "bar"}])
    assert data == {}


def test_preprocess_set_text_value_from_str_should_set_text_for_selected_nodes(shining):
    items = [{"key": "genres",
              "value": {
                  "foreach": ".//ul[@class='genres']/li",
                  "path": "./text()",
                  "reduce": reducers.first
              }}]
    data = extract(shining, items,
                   pre=[{"op": "set_text", "path": ".//ul[@class='genres']/li",
                         "text": "Foo"}])
    assert data == {'genres': ['Foo', 'Foo']}


def test_preprocess_set_text_value_from_path_should_set_text_for_selected_nodes(shining):
    items = [{"key": "genres",
              "value": {
                  "foreach": ".//ul[@class='genres']/li",
                  "path": "./text()",
                  "reduce": reducers.first
              }}]
    data = extract(shining, items,
                   pre=[{"op": "set_text", "path": ".//ul[@class='genres']/li",
                         "text": {
                             "path": "./text()",
                             "reduce": reducers.first,
                             "transform": str.lower
                         }}])
    assert data == {'genres': ['horror', 'drama']}


def test_preprocess_set_text_no_value_should_raise_error(shining):
    items = [{"key": "genres",
              "value": {
                  "foreach": ".//ul[@class='genres']/li",
                  "path": "./text()",
                  "reduce": reducers.first
              }}]
    with raises(ValueError):
        extract(shining, items,
                pre=[{"op": "set_text", "path": ".//ul[@class='genres']/li",
                      "text": {"path": "./@foo", "reduce": reducers.first}}])
