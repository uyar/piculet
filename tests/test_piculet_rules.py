from __future__ import absolute_import, division, print_function, unicode_literals

import os

from piculet import Path, Rule, Rules, build_tree, reducers


shining_file = os.path.join(os.path.dirname(__file__), '..', 'examples', 'shining.html')
shining = build_tree(open(shining_file).read())


def test_no_rules_should_return_empty_result():
    data = Rules([]).extract(shining)
    assert data == {}


def test_default_reducer_should_be_concat():
    rules = [Rule(key='full_title',
                  extractor=Path('//h1//text()'))]
    data = Rules(rules).extract(shining)
    assert data == {'full_title': 'The Shining (1980)'}


def test_reduce_by_lambda_should_be_ok():
    rules = [Rule(key='title',
                  extractor=Path('//title/text()', reduce=lambda xs: xs[0]))]
    data = Rules(rules).extract(shining)
    assert data == {'title': 'The Shining'}


def test_predefined_reducer_should_be_ok():
    rules = [Rule(key='title',
                  extractor=Path('//title/text()', reduce=reducers.first))]
    data = Rules(rules).extract(shining)
    assert data == {'title': 'The Shining'}


def test_reduced_value_should_be_transformable():
    rules = [Rule(key='year',
                  extractor=Path('//span[@class="year"]/text()',
                                 transform=int))]
    data = Rules(rules).extract(shining)
    assert data == {'year': 1980}


def test_multiple_rules_should_generate_multiple_items():
    rules = [Rule(key='title',
                  extractor=Path('//title/text()')),
             Rule('year',
                  extractor=Path('//span[@class="year"]/text()',
                                 transform=int))]
    data = Rules(rules).extract(shining)
    assert data == {'title': 'The Shining', 'year': 1980}


def test_item_with_no_data_should_be_excluded():
    rules = [Rule(key='title',
                  extractor=Path('//title/text()')),
             Rule(key='foo',
                  extractor=Path('//foo/text()'))]
    data = Rules(rules).extract(shining)
    assert data == {'title': 'The Shining'}


def test_item_with_empty_str_value_should_be_included():
    content = '<root><foo val=""/></root>'
    rules = [Rule(key='foo',
                  extractor=Path('//foo/@val'))]
    data = Rules(rules).extract(build_tree(content))
    assert data == {'foo': ''}


def test_item_with_zero_value_should_be_included():
    content = '<root><foo val="0"/></root>'
    rules = [Rule(key='foo',
                  extractor=Path('//foo/@val', transform=int))]
    data = Rules(rules).extract(build_tree(content))
    assert data == {'foo': 0}


def test_item_with_false_value_should_be_included():
    content = '<root><foo val=""/></root>'
    rules = [Rule(key='foo',
                  extractor=Path('//foo/@val', transform=bool))]
    data = Rules(rules).extract(build_tree(content))
    assert data == {'foo': False}


def test_multivalued_item_should_be_list():
    rules = [Rule(key='genres',
                  extractor=Path(foreach='//ul[@class="genres"]/li',
                                 path='./text()'))]
    data = Rules(rules).extract(shining)
    assert data == {'genres': ['Horror', 'Drama']}


def test_multivalued_items_should_be_transformable():
    rules = [Rule(key='genres',
                  extractor=Path(foreach='//ul[@class="genres"]/li',
                                 path='./text()', transform=lambda x: x.lower()))]
    data = Rules(rules).extract(shining)
    assert data == {'genres': ['horror', 'drama']}


def test_empty_values_should_be_excluded_from_multivalued_item_list():
    rules = [Rule(key='foos',
                  extractor=Path(foreach='//ul[@class="foos"]/li',
                                 path='./text()'))]
    data = Rules(rules).extract(shining)
    assert data == {}


def test_subrules_should_generate_subitems():
    rules = [
        Rule(key='director',
             extractor=Rules(
                 subrules=[
                     Rule(key='name',
                          extractor=Path('//div[@class="director"]//a/text()')),
                     Rule(key='link',
                          extractor=Path('//div[@class="director"]//a/@href'))
                 ]))
    ]
    data = Rules(rules).extract(shining)
    assert data == {'director': {'link': '/people/1', 'name': 'Stanley Kubrick'}}


def test_multivalued_subrules_should_generate_list_of_subitems():
    rules = [
        Rule(key='cast',
             extractor=Rules(
                 foreach='//table[@class="cast"]/tr',
                 subrules=[
                     Rule(key='name',
                          extractor=Path('./td[1]/a/text()')),
                     Rule(key='link',
                          extractor=Path('./td[1]/a/@href')),
                     Rule(key='character',
                          extractor=Path('./td[2]/text()'))
                 ]))
    ]
    data = Rules(rules).extract(shining)
    assert data == {'cast': [
        {'character': 'Jack Torrance', 'link': '/people/2', 'name': 'Jack Nicholson'},
        {'character': 'Wendy Torrance', 'link': '/people/3', 'name': 'Shelley Duvall'}
    ]}


def test_subitems_should_be_transformable():
    rules = [
        Rule(key='cast',
             extractor=Rules(
                 foreach='//table[@class="cast"]/tr',
                 subrules=[
                     Rule(key='name',
                          extractor=Path('./td[1]/a/text()')),
                     Rule(key='link',
                          extractor=Path('./td[1]/a/@href')),
                     Rule(key='character',
                          extractor=Path('./td[2]/text()'))
                 ],
                 transform=lambda x: x.get('name') + ' as ' + x.get('character')
             ))
    ]
    data = Rules(rules).extract(shining)
    assert data == {'cast': ['Jack Nicholson as Jack Torrance',
                             'Shelley Duvall as Wendy Torrance']}


def test_key_should_be_generatable_using_path():
    rules = [Rule(section='//div[@class="info"]',
                  key=Path('./h3/text()'),
                  extractor=Path('./p/text()'))]
    data = Rules(rules).extract(shining)
    assert data == {'Language:': 'English', 'Runtime:': '144 minutes'}


def test_generated_key_should_be_normalizable():
    rules = [Rule(section='//div[@class="info"]',
                  key=Path('./h3/text()', reduce=reducers.normalize),
                  extractor=Path('./p/text()'))]
    data = Rules(rules).extract(shining)
    assert data == {'language': 'English', 'runtime': '144 minutes'}


def test_generated_key_should_be_transformable():
    rules = [Rule(section='//div[@class="info"]',
                  key=Path('./h3/text()', reduce=reducers.normalize,
                           transform=lambda x: x.upper()),
                  extractor=Path('./p/text()'))]
    data = Rules(rules).extract(shining)
    assert data == {'LANGUAGE': 'English', 'RUNTIME': '144 minutes'}


def test_generated_key_none_should_be_excluded():
    rules = [Rule(section='//div[@class="info"]',
                  key=Path('./foo/text()'),
                  extractor=Path('./p/text()'))]
    data = Rules(rules).extract(shining)
    assert data == {}
