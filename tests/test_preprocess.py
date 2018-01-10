from __future__ import absolute_import, division, print_function, unicode_literals

from piculet import extract, preprocess


def test_root_none_should_return_empty_result(shining):
    pre = [{'op': 'root', 'path': '//foo'}]
    items = [{'key': 'title', 'value': {'path': '//title/text()'}}]
    data = extract(preprocess(shining, pre), items)
    assert data == {}


def test_root_multiple_should_return_empty_result(shining):
    pre = [{'op': 'root', 'path': '//div'}]
    items = [{'key': 'title', 'value': {'path': '//title/text()'}}]
    data = extract(preprocess(shining, pre), items)
    assert data == {}


def test_root_should_exclude_unselected_parts(shining):
    pre = [{'op': 'root', 'path': '//div[@class="director"]'}]
    items = [{'key': 'foo', 'value': {'path': '//h3/text()'}}]
    data = extract(preprocess(shining, pre), items)
    assert data == {'foo': 'Director:'}


def test_remove_should_remove_selected_node(shining):
    pre = [{'op': 'remove', 'path': '//tr[1]'}]
    items = [{'key': 'cast',
              'value': {
                  'foreach': '//table[@class="cast"]/tr',
                  'items': [
                      {'key': 'name', 'value': {'path': './td[1]/a/text()'}}
                  ]
              }}]
    data = extract(preprocess(shining, pre), items)
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
    data = extract(preprocess(shining, pre), items)
    assert data == {'cast': [{'name': 'Jack Nicholson'}, {'name': 'Shelley Duvall'}]}


def test_set_attr_value_from_str_should_set_attribute_for_selected_nodes(shining):
    pre = [{'op': 'set_attr', 'path': "//ul[@class='genres']/li",
            'name': 'foo', 'value': "bar"}]
    items = [{'key': 'genres',
              'value': {
                  'foreach': "//li[@foo='bar']",
                  'path': "./text()"
              }}]
    data = extract(preprocess(shining, pre), items)
    assert data == {'genres': ['Horror', 'Drama']}


def test_set_attr_value_from_path_should_set_attribute_for_selected_nodes(shining):
    pre = [{'op': 'set_attr', 'path': '//ul[@class="genres"]/li',
            'name': 'foo',
            'value': {'path': './text()'}}]
    items = [{'key': 'genres',
              'value': {
                  'foreach': '//li[@foo]',
                  'path': './@foo'
              }}]
    data = extract(preprocess(shining, pre), items)
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
    data = extract(preprocess(shining, pre), items)
    assert data == {}


def test_set_attr_name_from_path_should_set_attribute_for_selected_nodes(shining):
    pre = [{'op': 'set_attr', 'path': '//ul[@class="genres"]/li',
            'name': {'path': './text()'},
            'value': 'bar'}]
    items = [{'key': 'genres',
              'value': {
                  'foreach': '//li[@Horror]',
                  'path': './@Horror'
              }}]
    data = extract(preprocess(shining, pre), items)
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
    data = extract(preprocess(shining, pre), items)
    assert data == {}


def test_set_attr_selected_none_should_not_cause_error(shining):
    pre = [{'op': 'set_attr', 'path': '//foo', 'name': 'foo', 'value': 'bar'}]
    items = [{'key': 'genres',
              'value': {
                  'foreach': '//li[@foo="bar"]',
                  'path': './@foo'
              }}]
    data = extract(preprocess(shining, pre), items)
    assert data == {}


def test_set_text_value_from_str_should_set_text_for_selected_nodes(shining):
    pre = [{'op': 'set_text', 'path': '//ul[@class="genres"]/li',
            "text": 'Foo'}]
    items = [{'key': 'genres',
              'value': {
                  'foreach': '//ul[@class="genres"]/li',
                  'path': './text()'
              }}]
    data = extract(preprocess(shining, pre), items)
    assert data == {'genres': ['Foo', 'Foo']}


def test_set_text_value_from_path_should_set_text_for_selected_nodes(shining):
    pre = [{'op': 'set_text', 'path': '//ul[@class="genres"]/li',
            "text": {
                'path': './text()',
                'transform': lambda x: x.lower()
            }}]
    items = [{'key': 'genres',
              'value': {
                  'foreach': '//ul[@class="genres"]/li',
                  'path': './text()'
              }}]
    data = extract(preprocess(shining, pre), items)
    assert data == {'genres': ['horror', 'drama']}


def test_set_text_no_value_should_be_ignored(shining):
    pre = [{'op': 'set_text', 'path': '//ul[@class="genres"]/li',
            'text': {'path': './@foo'}}]
    items = [{'key': 'genres',
              'value': {
                  'foreach': '//ul[@class="genres"]/li',
                  'path': './text()'
              }}]
    data = extract(preprocess(shining, pre), items)
    assert data == {}
