from __future__ import absolute_import, division, print_function, unicode_literals

from pytest import raises

from piculet import reducers, scrape, transformers


def test_no_rules_should_return_empty_result(shining_content):
    data = scrape(shining_content, {'items': []})
    assert data == {}


def test_extracted_value_should_be_reduced(shining_content):
    items = [{'key': 'title',
              'value': {'path': '//title/text()', 'reduce': 'first'}}]
    data = scrape(shining_content, {'items': items})
    assert data == {'title': 'The Shining'}


def test_default_reducer_should_be_concat(shining_content):
    items = [{'key': 'full_title',
              'value': {'path': '//h1//text()'}}]
    data = scrape(shining_content, {'items': items})
    assert data == {'full_title': 'The Shining (1980)'}


def test_added_reducer_should_be_usable(shining_content):
    reducers.register('second', lambda x: x[1])
    items = [{'key': 'year',
              'value': {'path': '//h1//text()', 'reduce': 'second'}}]
    data = scrape(shining_content, {'items': items})
    assert data == {'year': '1980'}


def test_unknown_reducer_should_raise_error(shining_content):
    with raises(ValueError):
        items = [{'key': 'year',
                  'value': {'path': '//h1//text()', 'reduce': 'foo'}}]
        scrape(shining_content, {'items': items})


def test_reduced_value_should_be_transformable(shining_content):
    items = [{'key': 'year',
              'value': {'path': '//span[@class="year"]/text()', 'transform': 'int'}}]
    data = scrape(shining_content, {'items': items})
    assert data == {'year': 1980}


def test_added_transformer_should_be_usable(shining_content):
    transformers.register('year25', lambda x: int(x) + 25)
    items = [{'key': 'year',
              'value': {'path': '//span[@class="year"]/text()', 'transform': 'year25'}}]
    data = scrape(shining_content, {'items': items})
    assert data == {'year': 2005}


def test_unknown_transformer_should_raise_error(shining_content):
    with raises(ValueError):
        items = [{'key': 'year',
                  'value': {'path': '//span[@class="year"]/text()', 'transform': 'year42'}}]
        scrape(shining_content, {'items': items})


def test_multiple_rules_should_generate_multiple_items(shining_content):
    items = [{'key': 'title',
              'value': {'path': '//title/text()'}},
             {'key': 'year',
              'value': {'path': '//span[@class="year"]/text()', 'transform': 'int'}}]
    data = scrape(shining_content, {'items': items})
    assert data == {'title': 'The Shining', 'year': 1980}


def test_item_with_no_data_should_be_excluded(shining_content):
    items = [{'key': 'title',
              'value': {'path': '//title/text()'}},
             {'key': 'foo',
              'value': {'path': '//foo/text()'}}]
    data = scrape(shining_content, {'items': items})
    assert data == {'title': 'The Shining'}


def test_multivalued_item_should_be_list(shining_content):
    items = [{'key': 'genres',
              'value': {'foreach': '//ul[@class="genres"]/li',
                        'path': './text()'}}]
    data = scrape(shining_content, {'items': items})
    assert data == {'genres': ['Horror', 'Drama']}


def test_multivalued_items_should_be_transformable(shining_content):
    items = [{'key': 'genres',
              'value': {'foreach': '//ul[@class="genres"]/li',
                        'path': './text()', 'transform': 'lower'}}]
    data = scrape(shining_content, {'items': items})
    assert data == {'genres': ['horror', 'drama']}


def test_empty_values_should_be_excluded_from_multivalued_item_list(shining_content):
    items = [{'key': 'foos',
              'value': {'foreach': '//ul[@class="foos"]/li',
                        'path': './text()'}}]
    data = scrape(shining_content, {'items': items})
    assert data == {}


def test_subrules_should_generate_subitems(shining_content):
    items = [{'key': 'director',
              'value': {
                  'items': [{'key': 'name',
                             'value': {'path': '//div[@class="director"]//a/text()'}},
                            {'key': 'link',
                             'value': {'path': '//div[@class="director"]//a/@href'}}]
              }}]
    data = scrape(shining_content, {'items': items})
    assert data == {'director': {'link': '/people/1', 'name': 'Stanley Kubrick'}}


def test_multivalued_subrules_should_generate_list_of_subitems(shining_content):
    items = [{'key': 'cast',
              'value': {
                  'foreach': '//table[@class="cast"]/tr',
                  'items': [
                      {'key': 'name',
                       'value': {'path': './td[1]/a/text()'}},
                      {'key': 'character',
                       'value': {'path': './td[2]/text()'}}
                  ]
              }}]
    data = scrape(shining_content, {'items': items})
    assert data == {'cast': [
        {'character': 'Jack Torrance', 'name': 'Jack Nicholson'},
        {'character': 'Wendy Torrance', 'name': 'Shelley Duvall'}
    ]}


def test_subitems_should_be_transformable(shining_content):
    transformers.register('stars', lambda x: '%(name)s as %(character)s' % x)
    items = [{'key': 'cast',
              'value': {
                  'foreach': '//table[@class="cast"]/tr',
                  'items': [
                      {'key': 'name', 'value': {'path': './td[1]/a/text()'}},
                      {'key': 'character', 'value': {'path': './td[2]/text()'}}
                  ],
                  'transform': 'stars'
              }}]
    data = scrape(shining_content, {'items': items})
    assert data == {'cast': ['Jack Nicholson as Jack Torrance',
                             'Shelley Duvall as Wendy Torrance']}


def test_key_should_be_generatable_using_path(shining_content):
    items = [
        {
            'foreach': '//div[@class="info"]',
            'key': {'path': './h3/text()'},
            'value': {'path': './p/text()'}
        }
    ]
    data = scrape(shining_content, {'items': items})
    assert data == {'Language:': 'English', 'Runtime:': '144 minutes'}


def test_generated_key_should_be_normalizable(shining_content):
    items = [
        {
            'foreach': '//div[@class="info"]',
            'key': {'path': './h3/text()',
                    'reduce': 'normalize'},
            'value': {'path': './p/text()'}
        }
    ]
    data = scrape(shining_content, {'items': items})
    assert data == {'language': 'English', 'runtime': '144 minutes'}


def test_generated_key_should_be_transformable(shining_content):
    items = [
        {
            'foreach': '//div[@class="info"]',
            'key': {'path': './h3/text()',
                    'reduce': 'normalize',
                    'transform': 'upper'},
            'value': {'path': './p/text()'}
        }
    ]
    data = scrape(shining_content, {'items': items})
    assert data == {'LANGUAGE': 'English', 'RUNTIME': '144 minutes'}


def test_generated_key_none_should_be_excluded(shining_content):
    items = [
        {
            'foreach': '//div[@class="info"]',
            'key': {'path': './foo/text()'},
            'value': {'path': './p/text()'}
        }
    ]
    data = scrape(shining_content, {'items': items})
    assert data == {}


def test_tree_should_be_preprocessable(shining_content):
    pre = [{'op': 'set_text', 'path': '//ul[@class="genres"]/li', "text": 'Foo'}]
    items = [{'key': 'genres',
              'value': {
                  'foreach': '//ul[@class="genres"]/li',
                  'path': './text()'
              }}]
    data = scrape(shining_content, {'items': items, 'pre': pre})
    assert data == {'genres': ['Foo', 'Foo']}


def test_section_should_set_root_for_queries(shining_content):
    items = [{'key': 'director',
              'value': {
                  'section': '//div[@class="director"]//a',
                  'items': [{'key': 'name',
                             'value': {'path': './text()'}},
                            {'key': 'link',
                             'value': {'path': './@href'}}]
              }}]
    data = scrape(shining_content, {'items': items})
    assert data == {'director': {'link': '/people/1', 'name': 'Stanley Kubrick'}}


def test_section_no_roots_should_return_empty_result(shining_content):
    items = [{'key': 'director',
              'value': {
                  'section': '//foo',
                  'items': [{'key': 'name',
                             'value': {'path': './text()'}}]
              }}]
    data = scrape(shining_content, {'items': items})
    assert data == {}


def test_section_multiple_roots_should_raise_error(shining_content):
    with raises(ValueError):
        items = [{'key': 'director',
                  'value': {
                      'section': '//div',
                      'items': [{'key': 'name',
                                 'value': {'path': './text()'}}]
                  }}]
        scrape(shining_content, {'items': items})
