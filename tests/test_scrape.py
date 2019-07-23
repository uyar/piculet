import pytest

from pkgutil import find_loader

from piculet import scrape, transformers


LXML_AVAILABLE = find_loader("lxml") is not None


def test_empty_rules_should_return_empty_result(shining_content):
    data = scrape(shining_content, {"items": []})
    assert data == {}


def test_extracted_text_should_be_scalar(shining_content):
    items = [{"key": "title", "value": {"path": "//title/text()"}}]
    data = scrape(shining_content, {"items": items})
    assert data == {"title": "The Shining"}


def test_extracted_texts_should_be_concatenated(shining_content):
    items = [{"key": "full_title", "value": {"path": "//h1//text()"}}]
    data = scrape(shining_content, {"items": items})
    assert data == {"full_title": "The Shining (1980)"}


def test_extracted_texts_should_be_concatenated_using_given_separator(shining_content):
    items = [
        {
            "key": "cast_names",
            "value": {"path": '//table[@class="cast"]/tr/td[1]/a/text()', "sep": ", "},
        }
    ]
    data = scrape(shining_content, {"items": items})
    assert data == {"cast_names": "Jack Nicholson, Shelley Duvall"}


def test_extracted_value_should_be_transformable(shining_content):
    items = [
        {"key": "year", "value": {"path": '//span[@class="year"]/text()', "transform": "int"}}
    ]
    data = scrape(shining_content, {"items": items})
    assert data == {"year": 1980}


def test_added_transformer_should_be_usable(shining_content):
    transformers.underscore = lambda s: s.replace(" ", "_")
    items = [{"key": "title", "value": {"path": "//title/text()", "transform": "underscore"}}]
    data = scrape(shining_content, {"items": items})
    assert data == {"title": "The_Shining"}


def test_transformers_should_be_chainable(shining_content):
    transformers.century = lambda x: x // 100 + 1
    items = [
        {
            "key": "century",
            "value": {"path": '//span[@class="year"]/text()', "transform": "int|century"},
        }
    ]
    data = scrape(shining_content, {"items": items})
    assert data == {"century": 20}


def test_unknown_transformer_should_raise_error(shining_content):
    with pytest.raises(ValueError):
        items = [
            {
                "key": "year",
                "value": {"path": '//span[@class="year"]/text()', "transform": "year42"},
            }
        ]
        scrape(shining_content, {"items": items})


def test_shorthand_notation_should_be_path_and_transform(shining_content):
    items = [{"key": "year", "value": '//span[@class="year"]/text() | int'}]
    data = scrape(shining_content, {"items": items})
    assert data == {"year": 1980}


def test_multiple_rules_should_generate_multiple_items(shining_content):
    items = [
        {"key": "title", "value": {"path": "//title/text()"}},
        {"key": "year", "value": {"path": '//span[@class="year"]/text()', "transform": "int"}},
    ]
    data = scrape(shining_content, {"items": items})
    assert data == {"title": "The Shining", "year": 1980}


def test_item_with_no_data_should_be_excluded(shining_content):
    items = [
        {"key": "title", "value": {"path": "//title/text()"}},
        {"key": "foo", "value": {"path": "//foo/text()"}},
    ]
    data = scrape(shining_content, {"items": items})
    assert data == {"title": "The Shining"}


def test_multivalued_item_should_be_list(shining_content):
    items = [
        {"key": "genres", "value": {"foreach": '//ul[@class="genres"]/li', "path": "./text()"}}
    ]
    data = scrape(shining_content, {"items": items})
    assert data == {"genres": ["Horror", "Drama"]}


def test_multivalued_items_should_be_transformable(shining_content):
    items = [
        {
            "key": "genres",
            "value": {
                "foreach": '//ul[@class="genres"]/li',
                "path": "./text()",
                "transform": "lower",
            },
        }
    ]
    data = scrape(shining_content, {"items": items})
    assert data == {"genres": ["horror", "drama"]}


def test_empty_values_should_be_excluded_from_multivalued_item_list(shining_content):
    items = [
        {"key": "foos", "value": {"foreach": '//ul[@class="foos"]/li', "path": "./text()"}}
    ]
    data = scrape(shining_content, {"items": items})
    assert data == {}


def test_subrules_should_generate_subitems(shining_content):
    items = [
        {
            "key": "director",
            "value": {
                "items": [
                    {"key": "name", "value": {"path": '//div[@class="director"]//a/text()'}},
                    {"key": "link", "value": {"path": '//div[@class="director"]//a/@href'}},
                ]
            },
        }
    ]
    data = scrape(shining_content, {"items": items})
    assert data == {"director": {"link": "/people/1", "name": "Stanley Kubrick"}}


def test_multivalued_subrules_should_generate_list_of_subitems(shining_content):
    items = [
        {
            "key": "cast",
            "value": {
                "foreach": '//table[@class="cast"]/tr',
                "items": [
                    {"key": "name", "value": {"path": "./td[1]/a/text()"}},
                    {"key": "character", "value": {"path": "./td[2]/text()"}},
                ],
            },
        }
    ]
    data = scrape(shining_content, {"items": items})
    assert data == {
        "cast": [
            {"character": "Jack Torrance", "name": "Jack Nicholson"},
            {"character": "Wendy Torrance", "name": "Shelley Duvall"},
        ]
    }


def test_subitems_should_be_transformable(shining_content):
    transformers.stars = lambda x: "%(name)s as %(character)s" % x
    items = [
        {
            "key": "cast",
            "value": {
                "foreach": '//table[@class="cast"]/tr',
                "items": [
                    {"key": "name", "value": {"path": "./td[1]/a/text()"}},
                    {"key": "character", "value": {"path": "./td[2]/text()"}},
                ],
                "transform": "stars",
            },
        }
    ]
    data = scrape(shining_content, {"items": items})
    assert data == {
        "cast": ["Jack Nicholson as Jack Torrance", "Shelley Duvall as Wendy Torrance"]
    }


def test_key_should_be_generatable_using_path(shining_content):
    items = [
        {
            "foreach": '//div[@class="info"]',
            "key": {"path": "./h3/text()"},
            "value": {"path": "./p/text()"},
        }
    ]
    data = scrape(shining_content, {"items": items})
    assert data == {"Language:": "English", "Runtime:": "144 minutes"}


def test_generated_key_should_be_transformable(shining_content):
    items = [
        {
            "foreach": '//div[@class="info"]',
            "key": {"path": "./h3/text()", "transform": "normalize"},
            "value": {"path": "./p/text()"},
        }
    ]
    data = scrape(shining_content, {"items": items})
    assert data == {"language": "English", "runtime": "144 minutes"}


def test_generated_key_none_should_be_excluded(shining_content):
    items = [
        {
            "foreach": '//div[@class="info"]',
            "key": {"path": "./foo/text()"},
            "value": {"path": "./p/text()"},
        }
    ]
    data = scrape(shining_content, {"items": items})
    assert data == {}


def test_tree_should_be_preprocessable(shining_content):
    pre = [{"op": "set_text", "path": '//ul[@class="genres"]/li', "text": "Foo"}]
    items = [
        {"key": "genres", "value": {"foreach": '//ul[@class="genres"]/li', "path": "./text()"}}
    ]
    data = scrape(shining_content, {"items": items, "pre": pre})
    assert data == {"genres": ["Foo", "Foo"]}


def test_section_should_set_root_for_queries(shining_content):
    items = [
        {
            "key": "director",
            "value": {
                "section": '//div[@class="director"]//a',
                "items": [
                    {"key": "name", "value": {"path": "./text()"}},
                    {"key": "link", "value": {"path": "./@href"}},
                ],
            },
        }
    ]
    data = scrape(shining_content, {"items": items})
    assert data == {"director": {"link": "/people/1", "name": "Stanley Kubrick"}}


def test_section_no_roots_should_return_empty_result(shining_content):
    items = [
        {
            "key": "director",
            "value": {
                "section": "//foo",
                "items": [{"key": "name", "value": {"path": "./text()"}}],
            },
        }
    ]
    data = scrape(shining_content, {"items": items})
    assert data == {}


def test_section_multiple_roots_should_raise_error(shining_content):
    with pytest.raises(ValueError):
        items = [
            {
                "key": "director",
                "value": {
                    "section": "//div",
                    "items": [{"key": "name", "value": {"path": "./text()"}}],
                },
            }
        ]
        scrape(shining_content, {"items": items})


@pytest.mark.skipif(not LXML_AVAILABLE, reason="requires support for LXML")
def test_scrape_should_use_lxml_html_parser_if_requested(shining_content):
    content = shining_content.replace('<meta charset="utf-8"/>', '<meta charset="utf-8">')
    items = [{"key": "title", "value": {"path": "//title/text()"}}]
    data = scrape(content, {"items": items}, lxml_html=True)
    assert data == {"title": "The Shining"}


@pytest.mark.skipif(LXML_AVAILABLE, reason="wants exception if no LXML support")
def test_scrape_should_fail_for_lxml_html_parser_if_no_lxml_support(shining_content):
    with pytest.raises(RuntimeError) as e:
        scrape(shining_content, {}, lxml_html=True)
        assert "LXML not available" in str(e)


def test_unknown_preprocessor_should_raise_error(shining_content):
    with pytest.raises(ValueError):
        pre = [{"op": "foo", "path": "//tr[1]"}]
        scrape(shining_content, {"pre": pre})


def test_remove_should_remove_selected_element(shining_content):
    pre = [{"op": "remove", "path": "//tr[1]"}]
    items = [
        {
            "key": "cast",
            "value": {
                "foreach": '//table[@class="cast"]/tr',
                "items": [{"key": "name", "value": {"path": "./td[1]/a/text()"}}],
            },
        }
    ]
    data = scrape(shining_content, {"pre": pre, "items": items})
    assert data == {"cast": [{"name": "Shelley Duvall"}]}


def test_remove_selected_none_should_not_cause_error(shining_content):
    pre = [{"op": "remove", "path": "//tr[50]"}]
    items = [
        {
            "key": "cast",
            "value": {
                "foreach": '//table[@class="cast"]/tr',
                "items": [{"key": "name", "value": {"path": "./td[1]/a/text()"}}],
            },
        }
    ]
    data = scrape(shining_content, {"pre": pre, "items": items})
    assert data == {"cast": [{"name": "Jack Nicholson"}, {"name": "Shelley Duvall"}]}


def test_set_attr_value_from_str_should_set_attribute_for_selected_elements(shining_content):
    pre = [
        {"op": "set_attr", "path": "//ul[@class='genres']/li", "name": "foo", "value": "bar"}
    ]
    items = [{"key": "genres", "value": {"foreach": "//li[@foo='bar']", "path": "./text()"}}]
    data = scrape(shining_content, {"pre": pre, "items": items})
    assert data == {"genres": ["Horror", "Drama"]}


def test_set_attr_value_from_path_should_set_attribute_for_selected_elements(shining_content):
    pre = [
        {
            "op": "set_attr",
            "path": '//ul[@class="genres"]/li',
            "name": "foo",
            "value": {"path": "./text()"},
        }
    ]
    items = [{"key": "genres", "value": {"foreach": "//li[@foo]", "path": "./@foo"}}]
    data = scrape(shining_content, {"pre": pre, "items": items})
    assert data == {"genres": ["Horror", "Drama"]}


def test_set_attr_value_from_path_empty_value_should_be_ignored(shining_content):
    pre = [
        {
            "op": "set_attr",
            "path": '//ul[@class="genres"]/li',
            "name": "foo",
            "value": {"path": "./@bar"},
        }
    ]
    items = [{"key": "genres", "value": {"foreach": "//li[@foo]", "path": "./@foo"}}]
    data = scrape(shining_content, {"pre": pre, "items": items})
    assert data == {}


def test_set_attr_name_from_path_should_set_attribute_for_selected_elements(shining_content):
    pre = [
        {
            "op": "set_attr",
            "path": '//ul[@class="genres"]/li',
            "name": {"path": "./text()"},
            "value": "bar",
        }
    ]
    items = [{"key": "genres", "value": {"foreach": "//li[@Horror]", "path": "./@Horror"}}]
    data = scrape(shining_content, {"pre": pre, "items": items})
    assert data == {"genres": ["bar"]}


def test_set_attr_name_from_path_empty_value_should_be_ignored(shining_content):
    pre = [
        {
            "op": "set_attr",
            "path": '//ul[@class="genres"]/li',
            "name": {"path": "./@bar"},
            "value": "bar",
        }
    ]
    items = [{"key": "genres", "value": {"foreach": ".//li[@Horror]", "path": "./@Horror"}}]
    data = scrape(shining_content, {"pre": pre, "items": items})
    assert data == {}


def test_set_attr_selected_none_should_not_cause_error(shining_content):
    pre = [{"op": "set_attr", "path": "//foo", "name": "foo", "value": "bar"}]
    items = [{"key": "genres", "value": {"foreach": '//li[@foo="bar"]', "path": "./@foo"}}]
    data = scrape(shining_content, {"pre": pre, "items": items})
    assert data == {}


def test_set_text_value_from_str_should_set_text_for_selected_elements(shining_content):
    pre = [{"op": "set_text", "path": '//ul[@class="genres"]/li', "text": "Foo"}]
    items = [
        {"key": "genres", "value": {"foreach": '//ul[@class="genres"]/li', "path": "./text()"}}
    ]
    data = scrape(shining_content, {"pre": pre, "items": items})
    assert data == {"genres": ["Foo", "Foo"]}


def test_set_text_value_from_path_should_set_text_for_selected_elements(shining_content):
    pre = [
        {
            "op": "set_text",
            "path": '//ul[@class="genres"]/li',
            "text": {"path": "./text()", "transform": "lower"},
        }
    ]
    items = [
        {"key": "genres", "value": {"foreach": '//ul[@class="genres"]/li', "path": "./text()"}}
    ]
    data = scrape(shining_content, {"pre": pre, "items": items})
    assert data == {"genres": ["horror", "drama"]}


def test_set_text_empty_value_should_be_ignored(shining_content):
    pre = [{"op": "set_text", "path": '//ul[@class="genres"]/li', "text": {"path": "./@foo"}}]
    items = [
        {"key": "genres", "value": {"foreach": '//ul[@class="genres"]/li', "path": "./text()"}}
    ]
    data = scrape(shining_content, {"pre": pre, "items": items})
    assert data == {}
