from __future__ import absolute_import, division, print_function, unicode_literals

from pytest import raises

from piculet import extract, preprocess


def test_unknown_preprocessor_should_raise_error(shining):
    with raises(ValueError):
        pre = [{'op': 'foo', 'path': '//tr[1]'}]
        preprocess(shining, pre)


def test_remove_should_remove_selected_element(shining):
    pre = [{'op': 'remove', 'path': '//tr[1]'}]
    items = [{'key': 'cast',
              'value': {
                  'foreach': '//table[@class="cast"]/tr',
                  'items': [
                      {'key': 'name', 'value': {'path': './td[1]/a/text()'}}
                  ]
              }}]
    preprocess(shining, pre)
    data = extract(shining, items)
    assert data == {'cast': [{'name': 'Shelley Duvall'}]}


def test_remove_selected_none_should_not_cause_error(shining):
    pre = [{'op': 'remove', 'path': '//tr[50]'}]
    items = [{'key': 'cast',
              'value': {
                  'foreach': '//table[@class="cast"]/tr',
                  'items': [
                      {'key': 'name', 'value': {'path': './td[1]/a/text()'}}
                  ]
              }}]
    preprocess(shining, pre)
    data = extract(shining, items)
    assert data == {'cast': [{'name': 'Jack Nicholson'}, {'name': 'Shelley Duvall'}]}


def test_set_attr_value_from_str_should_set_attribute_for_selected_elements(shining):
    pre = [{'op': 'set_attr', 'path': "//ul[@class='genres']/li",
            'name': 'foo', 'value': "bar"}]
    items = [{'key': 'genres',
              'value': {
                  'foreach': "//li[@foo='bar']",
                  'path': "./text()"
              }}]
    preprocess(shining, pre)
    data = extract(shining, items)
    assert data == {'genres': ['Horror', 'Drama']}


def test_set_attr_value_from_path_should_set_attribute_for_selected_elements(shining):
    pre = [{'op': 'set_attr', 'path': '//ul[@class="genres"]/li',
            'name': 'foo',
            'value': {'path': './text()'}}]
    items = [{'key': 'genres',
              'value': {
                  'foreach': '//li[@foo]',
                  'path': './@foo'
              }}]
    preprocess(shining, pre)
    data = extract(shining, items)
    assert data == {'genres': ['Horror', 'Drama']}


def test_set_attr_value_from_path_no_value_should_be_ignored(shining):
    pre = [{'op': 'set_attr', 'path': '//ul[@class="genres"]/li',
            'name': 'foo',
            'value': {'path': './@bar'}}]
    items = [{'key': 'genres',
              'value': {
                  'foreach': '//li[@foo]',
                  'path': './@foo'
              }}]
    preprocess(shining, pre)
    data = extract(shining, items)
    assert data == {}


def test_set_attr_name_from_path_should_set_attribute_for_selected_elements(shining):
    pre = [{'op': 'set_attr', 'path': '//ul[@class="genres"]/li',
            'name': {'path': './text()'},
            'value': 'bar'}]
    items = [{'key': 'genres',
              'value': {
                  'foreach': '//li[@Horror]',
                  'path': './@Horror'
              }}]
    preprocess(shining, pre)
    data = extract(shining, items)
    assert data == {'genres': ['bar']}


def test_set_attr_name_from_path_no_value_should_be_ignored(shining):
    pre = [{'op': 'set_attr', 'path': '//ul[@class="genres"]/li',
            'name': {'path': './@bar'},
            'value': 'bar'}]
    items = [{'key': 'genres',
              'value': {
                  'foreach': './/li[@Horror]',
                  'path': './@Horror'
              }}]
    preprocess(shining, pre)
    data = extract(shining, items)
    assert data == {}


def test_set_attr_selected_none_should_not_cause_error(shining):
    pre = [{'op': 'set_attr', 'path': '//foo', 'name': 'foo', 'value': 'bar'}]
    items = [{'key': 'genres',
              'value': {
                  'foreach': '//li[@foo="bar"]',
                  'path': './@foo'
              }}]
    preprocess(shining, pre)
    data = extract(shining, items)
    assert data == {}


def test_set_text_value_from_str_should_set_text_for_selected_elements(shining):
    pre = [{'op': 'set_text', 'path': '//ul[@class="genres"]/li',
            "text": 'Foo'}]
    items = [{'key': 'genres',
              'value': {
                  'foreach': '//ul[@class="genres"]/li',
                  'path': './text()'
              }}]
    preprocess(shining, pre)
    data = extract(shining, items)
    assert data == {'genres': ['Foo', 'Foo']}


def test_set_text_value_from_path_should_set_text_for_selected_elements(shining):
    pre = [{'op': 'set_text', 'path': '//ul[@class="genres"]/li',
            "text": {
                'path': './text()',
                'transform': 'lower'
            }}]
    items = [{'key': 'genres',
              'value': {
                  'foreach': '//ul[@class="genres"]/li',
                  'path': './text()'
              }}]
    preprocess(shining, pre)
    data = extract(shining, items)
    assert data == {'genres': ['horror', 'drama']}


def test_set_text_no_value_should_be_ignored(shining):
    pre = [{'op': 'set_text', 'path': '//ul[@class="genres"]/li',
            'text': {'path': './@foo'}}]
    items = [{'key': 'genres',
              'value': {
                  'foreach': '//ul[@class="genres"]/li',
                  'path': './text()'
              }}]
    preprocess(shining, pre)
    data = extract(shining, items)
    assert data == {}
