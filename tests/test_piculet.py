from __future__ import absolute_import, division, print_function, unicode_literals

from pytest import raises

import os

from piculet import build_tree, extract, reducers, woodpecker, xpath


########################################
# xpath tests
########################################


generic_content = '<d><t1>foo</t1><t1 a="v"><t2>bar</t2></t1></d>'
generic_root = build_tree(generic_content)


def test_xpath_non_text_queries_should_return_nodes():
    selected = xpath(generic_root, ".//t1")
    assert [s.tag for s in selected] == ['t1', 't1']


def test_xpath_child_text_queries_should_return_strings():
    selected = xpath(generic_root, ".//t1/text()")
    assert selected == ['foo']


def test_xpath_descendant_text_queries_should_return_strings():
    selected = xpath(generic_root, ".//t1//text()")
    assert selected == ['foo', 'bar']


def test_xpath_attr_queries_should_return_strings():
    selected = xpath(generic_root, ".//t1/@a")
    assert selected == ['v']


########################################
# reducer tests
########################################


def test_reducer_first_should_return_first_item():
    assert reducers.first(['a', 'b', 'c']) == 'a'


def test_reducer_join_should_return_joined_items():
    assert reducers.join(['a', 'b', 'c']) == 'abc'


def test_reducer_clean_should_remove_extra_space():
    assert reducers.clean(['  a ', '   b', ' c ']) == 'a b c'


def test_reducer_clean_should_treat_nbsp_as_space():
    assert reducers.clean(['  a ', ' \xa0  b', ' c ']) == 'a b c'


def test_reducer_normalize_should_convert_to_lowercase():
    assert reducers.normalize(['A', 'B', 'C']) == 'abc'


def test_reducer_normalize_should_remove_nonalphanumeric_characters():
    assert reducers.normalize(['a+', '?b7', '{c}']) == 'ab7c'


def test_reducer_normalize_should_keep_underscores():
    assert reducers.normalize(['a_', 'b', 'c']) == 'a_bc'


def test_reducer_normalize_should_replace_spaces_with_underscores():
    assert reducers.normalize(['a', ' b', 'c']) == 'a_bc'



########################################
# woodpecker tests
########################################


people_content = '<p><p1><n>John Smith</n><a>42</a></p1><p2><n>Jane Doe</n></p2></p>'
people_root = build_tree(people_content)


def test_peck_no_reducer_should_raise_error():
    with raises(ValueError):
        woodpecker(path=".//n/text()")


def test_peck_unknown_predefined_reducer_should_raise_error():
    with raises(ValueError):
        woodpecker(path=".//n/text()", reducer="merge")


def test_peck_known_predefined_reducer_should_be_ok():
    pecker = woodpecker(path=".//n/text()", reduce=reducers.first)
    data = pecker(people_root)
    assert data == 'John Smith'


def test_peck_known_predefined_reducer_by_name_should_be_ok():
    pecker = woodpecker(path=".//n/text()", reducer="first")
    data = pecker(people_root)
    assert data == 'John Smith'


def test_peck_callable_reducer_should_be_ok():
    pecker = woodpecker(path=".//n/text()", reduce=lambda xs: xs[1])
    data = pecker(people_root)
    assert data == 'Jane Doe'


def test_peck_callable_reducer_should_take_precedence():
    pecker = woodpecker(path=".//n/text()", reducer="first", reduce=lambda xs: xs[1])
    data = pecker(people_root)
    assert data == 'Jane Doe'


def test_peck_non_matching_path_should_return_none():
    pecker = woodpecker(path=".//foo/text()", reducer="first")
    data = pecker(people_root)
    assert data is None


########################################
# extraction tests
########################################


shining_file = os.path.join(os.path.dirname(__file__), '..', 'examples', 'shining.html')
shining = build_tree(open(shining_file).read())


def test_extract_no_rules_should_return_empty_result():
    data = extract(shining, [])
    assert data == {}


def test_extract_unknown_value_generator_should_raise_error():
    items = [{"key": "title", "value": {"foo": ".//title/text()"}}]
    with raises(ValueError):
        extract(shining, items)


def test_extract_path_value_generator_with_missing_reducer_should_raise_error():
    items = [{"key": "title", "value": {"path": ".//title/text()"}}]
    with raises(ValueError):
        extract(shining, items)


def test_extract_reducer_by_lambda_should_be_ok():
    items = [{"key": "title", "value": {"path": ".//title/text()", "reduce": lambda xs: xs[0]}}]
    data = extract(shining, items)
    assert data == {'title': 'The Shining'}


def test_extract_predefined_reducer_should_be_ok():
    items = [{"key": "title", "value": {"path": ".//title/text()", "reduce": reducers.first}}]
    data = extract(shining, items)
    assert data == {'title': 'The Shining'}


def test_extract_predefined_reducer_by_name_first_should_be_ok():
    items = [{"key": "title", "value": {"path": ".//title/text()", "reducer": "first"}}]
    data = extract(shining, items)
    assert data == {'title': 'The Shining'}


def test_extract_predefined_reducer_by_name_join_should_be_ok():
    items = [{"key": "full_title", "value": {"path": ".//h1//text()", "reducer": "join"}}]
    data = extract(shining, items)
    assert data == {'full_title': 'The Shining (1980)'}


def test_extract_predefined_reducer_by_name_clean_should_be_ok():
    items = [{"key": "review",
              "value": {"path": ".//div[@class='review']//text()", "reducer": "clean"}}]
    data = extract(shining, items)
    assert data == {'review': 'Fantastic movie. Definitely recommended.'}


def test_extract_multiple_rules_should_generate_multiple_items():
    items = [{"key": "title",
              "value": {"path": ".//title/text()", "reduce": reducers.first}},
             {"key": "year",
              "value": {"path": ".//span[@class='year']/text()", "reduce": reducers.first}}]
    data = extract(shining, items)
    assert data == {'title': 'The Shining', 'year': '1980'}


def test_extract_items_with_no_data_should_be_excluded():
    items = [{"key": "title",
              "value": {"path": ".//title/text()", "reduce": reducers.first}},
             {"key": "foo",
              "value": {"path": ".//foo/text()", "reduce": reducers.first}}]
    data = extract(shining, items)
    assert data == {'title': 'The Shining'}


def test_extract_transforming_should_be_applied_after_reducing():
    items = [{"key": "year",
              "value": {"path": ".//span[@class='year']/text()",
                        "reduce": reducers.first,
                        "transform": int}}]
    data = extract(shining, items)
    assert data == {'year': 1980}


def test_extract_multivalued_item_should_be_list():
    items = [{"key": "genres",
              "value": {"foreach": ".//ul[@class='genres']/li",
                        "path": "./text()",
                        "reduce": reducers.first}}]
    data = extract(shining, items)
    assert data == {'genres': ['Horror', 'Drama']}


def test_extract_multivalued_item_empty_should_be_excluded():
    items = [{"key": "foos",
              "value": {"foreach": ".//ul[@class='foos']/li",
                        "path": "./text()",
                        "reduce": reducers.first}}]
    data = extract(shining, items)
    assert data == {}


def test_extract_subrules_should_generate_submappings():
    items = [{"key": "director",
              "value": {
                  "items": [{"key": "name",
                             "value": {"path": ".//div[@class='director']//a/text()",
                                       "reduce": reducers.first}},
                            {"key": "link",
                             "value": {"path": ".//div[@class='director']//a/@href",
                                       "reduce": reducers.first}}]
              }}]
    data = extract(shining, items)
    assert data == {'director': {'link': '/people/1', 'name': 'Stanley Kubrick'}}


def test_extract_multivalued_subrules_should_be_allowed():
    items = [{"key": "cast",
              "value": {
                  "foreach": ".//table[@class='cast']/tr",
                  "items": [
                      {"key": "name",
                       "value": {"path": "./td[1]/a/text()",
                                 "reduce": reducers.first}},
                      {"key": "link",
                       "value": {"path": "./td[1]/a/@href",
                                 "reduce": reducers.first}},
                      {"key": "character",
                       "value": {"path": "./td[2]/text()",
                                 "reduce": reducers.first}}
                  ]
              }}]
    data = extract(shining, items)
    assert data == {'cast': [
        {'character': 'Jack Torrance', 'link': '/people/2', 'name': 'Jack Nicholson'},
        {'character': 'Wendy Torrance', 'link': '/people/3', 'name': 'Shelley Duvall'}
    ]}


def test_extract_subitems_should_be_transformable():
    items = [{"key": "cast",
              "value": {
                  "foreach": ".//table[@class='cast']/tr",
                  "items": [
                      {"key": "name",
                       "value": {"path": "./td[1]/a/text()",
                                 "reduce": reducers.first}},
                      {"key": "character",
                       "value": {"path": "./td[2]/text()",
                                 "reduce": reducers.first}}
                  ],
                  "transform": lambda x: x.get('name') + ' as ' + x.get('character')
              }}]
    data = extract(shining, items)
    assert data == {'cast': ['Jack Nicholson as Jack Torrance',
                             'Shelley Duvall as Wendy Torrance']}


def test_extract_generated_key_path_with_missing_reducer_should_raise_error():
    items = [
        {
            "foreach": ".//div[@class='info']",
            "key": {"path": "./h3/text()"},
            "value": {"path": "./p/text()",
                      "reduce": reducers.first}
        }
    ]
    with raises(ValueError):
        extract(shining, items)


def test_extract_generated_key_path_and_reducer_should_be_ok():
    items = [
        {
            "foreach": ".//div[@class='info']",
            "key": {"path": "./h3/text()",
                    "reduce": reducers.first},
            "value": {"path": "./p/text()",
                      "reduce": reducers.first}
        }
    ]
    data = extract(shining, items)
    assert data == {'Language:': 'English', 'Runtime:': '144 minutes'}


def test_extract_generated_key_normalize_reducer_should_be_ok():
    items = [
        {
            "foreach": ".//div[@class='info']",
            "key": {"path": "./h3/text()",
                    "reduce": reducers.normalize},
            "value": {"path": "./p/text()",
                      "reduce": reducers.first}
        }
    ]
    data = extract(shining, items)
    assert data == {'language': 'English', 'runtime': '144 minutes'}


def test_extract_generated_key_should_be_transformable():
    items = [
        {
            "foreach": ".//div[@class='info']",
            "key": {"path": "./h3/text()",
                    "reduce": reducers.normalize,
                    "transform": lambda x: x.upper()},
            "value": {"path": "./p/text()",
                      "reduce": reducers.first}
        }
    ]
    data = extract(shining, items)
    assert data == {'LANGUAGE': 'English', 'RUNTIME': '144 minutes'}
