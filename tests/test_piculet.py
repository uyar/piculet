from __future__ import absolute_import, division, print_function, unicode_literals

import os

from piculet import build_tree, extract, reducers


shining_file = os.path.join(os.path.dirname(__file__), '..', 'examples', 'shining.html')
shining = build_tree(open(shining_file).read())


def test_no_rules_should_return_empty_result():
    data = extract(shining, [])
    assert data == {}


def test_default_reducer_should_be_concat():
    items = [{'key': 'full_title',
              'value': {'path': '//h1//text()'}}]
    data = extract(shining, items)
    assert data == {'full_title': 'The Shining (1980)'}


def test_reduce_by_lambda_should_be_ok():
    items = [{'key': 'title',
              'value': {'path': '//title/text()',
                        'reduce': lambda xs: xs[0]}}]
    data = extract(shining, items)
    assert data == {'title': 'The Shining'}


def test_predefined_reducer_should_be_ok():
    items = [{'key': 'title',
              'value': {'path': '//title/text()',
                        'reduce': reducers.first}}]
    data = extract(shining, items)
    assert data == {'title': 'The Shining'}


def test_predefined_reducer_by_name_should_be_ok():
    items = [{'key': 'title',
              'value': {'path': '//title/text()',
                        'reducer': 'first'}}]
    data = extract(shining, items)
    assert data == {'title': 'The Shining'}


def test_callable_reducer_should_take_precedence():
    items = [{'key': 'full_title',
              'value': {'path': '//h1//text()',
                        'reducer': 'concat',
                        'reduce': reducers.first}}]
    data = extract(shining, items)
    assert data == {'full_title': 'The Shining ('}


def test_transforming_should_be_applied_after_reducing():
    items = [{'key': 'year',
              'value': {'path': '//span[@class="year"]/text()',
                        'transform': int}}]
    data = extract(shining, items)
    assert data == {'year': 1980}


def test_multiple_rules_should_generate_multiple_items():
    items = [{'key': 'title',
              'value': {'path': '//title/text()'}},
             {'key': 'year',
              'value': {'path': '//span[@class="year"]/text()'}}]
    data = extract(shining, items)
    assert data == {'title': 'The Shining', 'year': '1980'}


def test_item_with_no_data_should_be_excluded():
    items = [{'key': 'title',
              'value': {'path': '//title/text()'}},
             {'key': 'foo',
              'value': {'path': '//foo/text()'}}]
    data = extract(shining, items)
    assert data == {'title': 'The Shining'}


def test_item_with_empty_str_value_should_be_included():
    content = '<root><foo val=""/></root>'
    items = [{'key': 'foo',
              'value': {'path': '//foo/@val'}}]
    data = extract(build_tree(content), items)
    assert data == {'foo': ''}


def test_item_with_zero_value_should_be_included():
    content = '<root><foo val="0"/></root>'
    items = [{'key': 'foo',
              'value': {'path': '//foo/@val',
                        'transform': int}}]
    data = extract(build_tree(content), items)
    assert data == {'foo': 0}


def test_item_with_false_value_should_be_included():
    content = '<root><foo val=""/></root>'
    items = [{'key': 'foo',
              'value': {'path': '//foo/@val',
                        'transform': bool}}]
    data = extract(build_tree(content), items)
    assert data == {'foo': False}


def test_multivalued_item_should_be_list():
    items = [{'key': 'genres',
              'value': {'foreach': '//ul[@class="genres"]/li',
                        'path': './text()'}}]
    data = extract(shining, items)
    assert data == {'genres': ['Horror', 'Drama']}


def test_multivalued_items_should_be_transformable():
    items = [{'key': 'genres',
              'value': {'foreach': '//ul[@class="genres"]/li',
                        'path': './text()',
                        'transform': lambda x: x.lower()}}]
    data = extract(shining, items)
    assert data == {'genres': ['horror', 'drama']}


def test_empty_values_should_be_excluded_from_multivalued_item_list():
    items = [{'key': 'foos',
              'value': {'foreach': '//ul[@class="foos"]/li',
                        'path': './text()'}}]
    data = extract(shining, items)
    assert data == {}


def test_subrules_should_generate_subitems():
    items = [{'key': 'director',
              'value': {
                  'items': [{'key': 'name',
                             'value': {'path': '//div[@class="director"]//a/text()'}},
                            {'key': 'link',
                             'value': {'path': '//div[@class="director"]//a/@href'}}]
              }}]
    data = extract(shining, items)
    assert data == {'director': {'link': '/people/1', 'name': 'Stanley Kubrick'}}


def test_multivalued_subrules_should_generate_list_of_subitems():
    items = [{'key': 'cast',
              'value': {
                  'foreach': '//table[@class="cast"]/tr',
                  'items': [
                      {'key': 'name',
                       'value': {'path': './td[1]/a/text()'}},
                      {'key': 'link',
                       'value': {'path': './td[1]/a/@href'}},
                      {'key': 'character',
                       'value': {'path': './td[2]/text()'}}
                  ]
              }}]
    data = extract(shining, items)
    assert data == {'cast': [
        {'character': 'Jack Torrance', 'link': '/people/2', 'name': 'Jack Nicholson'},
        {'character': 'Wendy Torrance', 'link': '/people/3', 'name': 'Shelley Duvall'}
    ]}


def test_subitems_should_be_transformable():
    items = [{'key': 'cast',
              'value': {
                  'foreach': '//table[@class="cast"]/tr',
                  'items': [
                      {'key': 'name', 'value': {'path': './td[1]/a/text()'}},
                      {'key': 'character', 'value': {'path': './td[2]/text()'}}
                  ],
                  'transform': lambda x: x.get('name') + ' as ' + x.get('character')
              }}]
    data = extract(shining, items)
    assert data == {'cast': ['Jack Nicholson as Jack Torrance',
                             'Shelley Duvall as Wendy Torrance']}


def test_key_should_be_generatable_using_path():
    items = [
        {
            'section': '//div[@class="info"]',
            'key': {'path': './h3/text()'},
            'value': {'path': './p/text()'}
        }
    ]
    data = extract(shining, items)
    assert data == {'Language:': 'English', 'Runtime:': '144 minutes'}


def test_generated_key_should_be_normalizable():
    items = [
        {
            'section': '//div[@class="info"]',
            'key': {'path': './h3/text()',
                    'reduce': reducers.normalize},
            'value': {'path': './p/text()'}
        }
    ]
    data = extract(shining, items)
    assert data == {'language': 'English', 'runtime': '144 minutes'}


def test_generated_key_should_be_transformable():
    items = [
        {
            'section': '//div[@class="info"]',
            'key': {'path': './h3/text()',
                    'reduce': reducers.normalize,
                    'transform': lambda x: x.upper()},
            'value': {'path': './p/text()'}
        }
    ]
    data = extract(shining, items)
    assert data == {'LANGUAGE': 'English', 'RUNTIME': '144 minutes'}


def test_generated_key_none_should_be_excluded():
    items = [
        {
            'section': '//div[@class="info"]',
            'key': {'path': './foo/text()'},
            'value': {'path': './p/text()'}
        }
    ]
    data = extract(shining, items)
    assert data == {}
