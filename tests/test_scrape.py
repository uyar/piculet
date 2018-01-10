from __future__ import absolute_import, division, print_function, unicode_literals

from piculet import reducers, scrape


def test_no_rules_should_return_empty_result(shining_content):
    data = scrape(shining_content, {})
    assert data == {}


def test_no_rule_items_should_return_empty_result(shining_content):
    data = scrape(shining_content, {'items': []})
    assert data == {}


def test_default_reducer_should_be_concat(shining_content):
    items = [{'key': 'full_title',
              'value': {'path': '//h1//text()'}}]
    data = scrape(shining_content, {'items': items})
    assert data == {'full_title': 'The Shining (1980)'}


def test_reduce_by_lambda_should_be_ok(shining_content):
    items = [{'key': 'title',
              'value': {'path': '//title/text()', 'reduce': lambda xs: xs[0]}}]
    data = scrape(shining_content, {'items': items})
    assert data == {'title': 'The Shining'}


def test_predefined_reducer_should_be_ok(shining_content):
    items = [{'key': 'title',
              'value': {'path': '//title/text()', 'reduce': reducers.first}}]
    data = scrape(shining_content, {'items': items})
    assert data == {'title': 'The Shining'}


def test_predefined_reducer_by_name_should_be_ok(shining_content):
    items = [{'key': 'title',
              'value': {'path': '//title/text()', 'reducer': 'first'}}]
    data = scrape(shining_content, {'items': items})
    assert data == {'title': 'The Shining'}


def test_callable_reducer_should_take_precedence(shining_content):
    items = [{'key': 'full_title',
              'value': {'path': '//h1//text()', 'reducer': 'concat', 'reduce': reducers.first}}]
    data = scrape(shining_content, {'items': items})
    assert data == {'full_title': 'The Shining ('}


def test_reduced_value_should_be_transformable(shining_content):
    items = [{'key': 'year',
              'value': {'path': '//span[@class="year"]/text()', 'transform': int}}]
    data = scrape(shining_content, {'items': items})
    assert data == {'year': 1980}


def test_multiple_rules_should_generate_multiple_items(shining_content):
    items = [{'key': 'title',
              'value': {'path': '//title/text()'}},
             {'key': 'year',
              'value': {'path': '//span[@class="year"]/text()', 'transform': int}}]
    data = scrape(shining_content, {'items': items})
    assert data == {'title': 'The Shining', 'year': 1980}


def test_item_with_no_data_should_be_excluded(shining_content):
    items = [{'key': 'title',
              'value': {'path': '//title/text()'}},
             {'key': 'foo',
              'value': {'path': '//foo/text()'}}]
    data = scrape(shining_content, {'items': items})
    assert data == {'title': 'The Shining'}


def test_item_with_empty_str_value_should_be_included():
    content = '<root><foo val=""/></root>'
    items = [{'key': 'foo',
              'value': {'path': '//foo/@val'}}]
    data = scrape(content, {'items': items})
    assert data == {'foo': ''}


def test_item_with_zero_value_should_be_included():
    content = '<root><foo val="0"/></root>'
    items = [{'key': 'foo',
              'value': {'path': '//foo/@val', 'transform': int}}]
    data = scrape(content, {'items': items})
    assert data == {'foo': 0}


def test_item_with_false_value_should_be_included():
    content = '<root><foo val=""/></root>'
    items = [{'key': 'foo',
              'value': {'path': '//foo/@val', 'transform': bool}}]
    data = scrape(content, {'items': items})
    assert data == {'foo': False}


def test_multivalued_item_should_be_list(shining_content):
    items = [{'key': 'genres',
              'value': {'foreach': '//ul[@class="genres"]/li',
                        'path': './text()'}}]
    data = scrape(shining_content, {'items': items})
    assert data == {'genres': ['Horror', 'Drama']}


def test_multivalued_items_should_be_transformable(shining_content):
    items = [{'key': 'genres',
              'value': {'foreach': '//ul[@class="genres"]/li',
                        'path': './text()', 'transform': lambda x: x.lower()}}]
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
    items = [{'key': 'cast',
              'value': {
                  'foreach': '//table[@class="cast"]/tr',
                  'items': [
                      {'key': 'name', 'value': {'path': './td[1]/a/text()'}},
                      {'key': 'character', 'value': {'path': './td[2]/text()'}}
                  ],
                  'transform': lambda x: '%(name)s as %(character)s' % x
              }}]
    data = scrape(shining_content, {'items': items})
    assert data == {'cast': ['Jack Nicholson as Jack Torrance',
                             'Shelley Duvall as Wendy Torrance']}


def test_key_should_be_generatable_using_path(shining_content):
    items = [
        {
            'section': '//div[@class="info"]',
            'key': {'path': './h3/text()'},
            'value': {'path': './p/text()'}
        }
    ]
    data = scrape(shining_content, {'items': items})
    assert data == {'Language:': 'English', 'Runtime:': '144 minutes'}


def test_generated_key_should_be_normalizable(shining_content):
    items = [
        {
            'section': '//div[@class="info"]',
            'key': {'path': './h3/text()',
                    'reduce': reducers.normalize},
            'value': {'path': './p/text()'}
        }
    ]
    data = scrape(shining_content, {'items': items})
    assert data == {'language': 'English', 'runtime': '144 minutes'}


def test_generated_key_should_be_transformable(shining_content):
    items = [
        {
            'section': '//div[@class="info"]',
            'key': {'path': './h3/text()',
                    'reduce': reducers.normalize,
                    'transform': lambda x: x.upper()},
            'value': {'path': './p/text()'}
        }
    ]
    data = scrape(shining_content, {'items': items})
    assert data == {'LANGUAGE': 'English', 'RUNTIME': '144 minutes'}


def test_generated_key_none_should_be_excluded(shining_content):
    items = [
        {
            'section': '//div[@class="info"]',
            'key': {'path': './foo/text()'},
            'value': {'path': './p/text()'}
        }
    ]
    data = scrape(shining_content, {'items': items})
    assert data == {}
