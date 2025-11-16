import pytest

import json
from pathlib import Path

import lxml.etree

from piculet import JSONPath, XMLPath, load_spec, scrape


MOVIE_XML_SPEC_FILE = Path(__file__).parent / "movie_xml_spec.json"
MOVIE_XML_SPEC = json.loads(MOVIE_XML_SPEC_FILE.read_text(encoding="utf-8"))
MOVIE_XML = Path(__file__).with_name("shining.html").read_text(encoding="utf-8")

MOVIE_JSON_SPEC_FILE = Path(__file__).with_name("movie_json_spec.json")
MOVIE_JSON_SPEC = json.loads(MOVIE_JSON_SPEC_FILE.read_text(encoding="utf-8"))
MOVIE_JSON = Path(__file__).with_name("shining.json").read_text(encoding="utf-8")


TRANSFORMERS = {
    "id_from_link": lambda x: int(x.split("/")[-1]),
    "lower": str.lower,
    "remove_spaces": lambda x: x.replace(" ", ""),
    "stars": lambda x: "%(name)s as %(character)s" % x,
    "titlecase": str.title,
}

PREPROCESSORS = {
    "empty_map": lambda _: {},
    "empty_tree": lambda _: lxml.etree.fromstring("<root/>"),
    "first_submap": lambda x: x.get("info", {}),
    "first_subtree": lambda x: x.xpath('./*[1]')[0],
    "id": lambda x: x,
}

POSTPROCESSORS = {
    "id": lambda x: x,
    "shorten": lambda x: {k[:-1]: v[:-1] for k, v in x.items()},
}


def test_load_spec_should_load_preprocess_from_str():
    spec = load_spec(MOVIE_XML_SPEC | {"pre": ["empty_map"], "rules": []}, preprocessors=PREPROCESSORS)
    assert spec.preprocessors[0]({"answer": 42}) == {}


def test_load_spec_should_raise_error_for_unknown_preprocess():
    with pytest.raises(KeyError):
        _ = load_spec(MOVIE_XML_SPEC | {"pre": ["UNKNOWN"], "rules": []}, preprocessors=PREPROCESSORS)


def test_load_spec_should_load_postprocess_from_str():
    spec = load_spec(MOVIE_XML_SPEC | {"post": ["shorten"], "rules": []}, postprocessors=POSTPROCESSORS)
    assert spec.postprocessors[0]({"genre": "Horror"}) == {"genr": "Horro"}


def test_load_spec_should_raise_error_for_unknown_postprocess():
    with pytest.raises(KeyError):
        _ = load_spec(MOVIE_XML_SPEC | {"post": ["UNKNOWN"], "rules": []}, postprocessors=POSTPROCESSORS)


def test_load_spec_should_load_transform_from_str():
    rules = [{"key": "k", "extractor": {"path": "/", "transforms": ["lower"]}}]
    spec = load_spec(MOVIE_XML_SPEC | {"rules": rules}, transformers=TRANSFORMERS)
    assert spec.rules[0].extractor.transformers[0]("Horror") == "horror"


def test_load_spec_should_raise_error_for_unknown_transform():
    rules = [{"key": "k", "extractor": {"path": "/", "transforms": ["UNKNOWN"]}}]
    with pytest.raises(KeyError):
        _ = load_spec(MOVIE_XML_SPEC | {"rules": rules}, transformers=TRANSFORMERS)


def test_load_spec_should_load_xml_path_from_str():
    rules = [{"key": "k", "extractor": {"path": "/"}}]
    spec = load_spec(MOVIE_XML_SPEC | {"rules": rules})
    assert isinstance(spec.rules[0].extractor.path, XMLPath)


def test_load_spec_should_load_json_path_from_str():
    rules = [{"key": "k", "extractor": {"path": "p"}}]
    spec = load_spec(MOVIE_JSON_SPEC | {"rules": rules})
    assert isinstance(spec.rules[0].extractor.path, JSONPath)


@pytest.mark.parametrize(("content", "skel"), [
    (MOVIE_XML, MOVIE_XML_SPEC),
    (MOVIE_JSON, MOVIE_JSON_SPEC),
])
def test_scrape_should_produce_empty_result_for_empty_rules(content, skel):
    spec = load_spec(skel | {"rules": []})
    assert scrape(content, spec) == {}


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {"key": "title", "extractor": {"path": "//title/text()"}}
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {"key": "title", "extractor": {"path": "title"}}
    ]),
])
def test_scrape_should_produce_scalar_value(content, skel, rules):
    spec = load_spec(skel | {"rules": rules})
    assert scrape(content, spec) == {"title": "The Shining"}


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {"key": "title", "extractor": {"path": "//title/text()"}},
        {"key": "country", "extractor": {"path": "//div[@class='info'][1]/p/text()"}}
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {"key": "title", "extractor": {"path": "title"}},
        {"key": "country", "extractor": {"path": "info.production[0].value"}}
    ]),
])
def test_scrape_should_produce_multiple_items_for_multiple_rules(content, skel, rules):
    spec = load_spec(skel | {"rules": rules})
    assert scrape(content, spec) == {"title": "The Shining", "country": "United States"}


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {"key": "title", "extractor": {"path": "//title/text()"}},
        {"key": "foo", "extractor": {"path": "//foo/text()"}}
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {"key": "title", "extractor": {"path": "title"}},
        {"key": "foo", "extractor": {"path": "foo"}}
    ]),
])
def test_scrape_should_exclude_data_for_rules_with_no_result(content, skel, rules):
    spec = load_spec(skel | {"rules": rules})
    assert scrape(content, spec) == {"title": "The Shining"}


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {"key": "title", "extractor": {"path": "//title/text()"}, "transforms": ["lower"]}
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {"key": "title", "extractor": {"path": "title"}, "transforms": ["lower"]}
    ]),
])
def test_scrape_should_transform_result(content, skel, rules):
    spec = load_spec(skel | {"rules": rules}, transformers=TRANSFORMERS)
    assert scrape(content, spec) == {"title": "the shining"}


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {
            "key": "title",
            "extractor": {"path": "//title/text()"},
            "transforms": ["remove_spaces", "titlecase"]
        }
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {
            "key": "title",
            "extractor": {"path": "title"},
            "transforms": ["remove_spaces", "titlecase"]
        }
    ]),
])
def test_scrape_should_apply_transforms_in_order(content, skel, rules):
    spec = load_spec(skel | {"rules": rules}, transformers=TRANSFORMERS)
    assert scrape(content, spec) == {"title": "Theshining"}


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {
            "key": "genres",
            "extractor": {"foreach": "//ul[@class='genres']/li", "path": "./text()"}
        }
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {
            "key": "genres",
            "extractor": {"foreach": "genres[*]", "path": "name"}
        }
    ]),
])
def test_scrape_should_produce_list_for_multivalued_rule(content, skel, rules):
    spec = load_spec(skel | {"rules": rules})
    assert scrape(content, spec) == {"genres": ["Horror", "Drama"]}


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {
            "key": "foos",
            "extractor": {"foreach": "//ul[@class='foos']/li", "path": "./text()"}
        }
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {
            "key": "foos",
            "extractor": {"foreach": "foos[*]", "path": "text"}
        }
    ]),
])
def test_scrape_should_exclude_empty_items_in_multivalued_rule_results(content, skel, rules):
    spec = load_spec(skel | {"rules": rules})
    assert scrape(content, spec) == {}


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {
            "key": "genres",
            "extractor": {
                "foreach": "//ul[@class='genres']/li",
                "path": "./text()",
                "transforms": ["lower"]
            },
        }
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {
            "key": "genres",
            "extractor": {
                "foreach": "genres[*]",
                "path": "name",
                "transforms": ["lower"]
            }
        }
    ]),
])
def test_scrape_should_transform_each_value_in_multivalued_result(content, skel, rules):
    spec = load_spec(skel | {"rules": rules}, transformers=TRANSFORMERS)
    assert scrape(content, spec) == {"genres": ["horror", "drama"]}


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {
            "key": "director",
            "extractor": {
                "rules": [
                    {
                        "key": "name",
                        "extractor": {"path": "//div[@class='director']//a/text()"}
                    },
                    {
                        "key": "id",
                        "extractor": {"path": "//div[@class='director']//a/@href"},
                        "transforms": ["id_from_link"]
                    }
                ]
            }
        }
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {
            "key": "director",
            "extractor": {
                "rules": [
                    {"key": "name", "extractor": {"path": "director.name"}},
                    {"key": "id", "extractor": {"path": "director.id"}}
                ]
            }
        }
    ]),
])
def test_scrape_should_produce_subitems_for_subrules(content, skel, rules):
    spec = load_spec(skel | {"rules": rules}, transformers=TRANSFORMERS)
    assert scrape(content, spec) == {"director": {"name": "Stanley Kubrick", "id": 1}}


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {
            "key": "cast",
            "extractor": {
                "foreach": "//table[@class='cast']/tr",
                "rules": [
                    {"key": "name", "extractor": {"path": "./td[1]/a/text()"}},
                    {"key": "character", "extractor": {"path": "./td[2]/text()"}}
                ]
            }
        }
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {
            "key": "cast",
            "extractor": {
                "foreach": "cast[*]",
                "rules": [
                    {"key": "name", "extractor": {"path": "name"}},
                    {"key": "character", "extractor": {"path": "character"}}
                ]
            }
        }
    ]),
])
def test_scrape_should_produce_subitem_lists_for_multivalued_subrules(content, skel, rules):
    spec = load_spec(skel | {"rules": rules})
    assert scrape(content, spec) == {
        "cast": [
            {"name": "Jack Nicholson", "character": "Jack Torrance"},
            {"name": "Shelley Duvall", "character": "Wendy Torrance"}
        ]
    }


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {
            "key": "cast",
            "extractor": {
                "foreach": "//table[@class='cast']/tr",
                "rules": [
                    {"key": "name", "extractor": {"path": "./td[1]/a/text()"}},
                    {"key": "character", "extractor": {"path": "./td[2]/text()"}}
                ],
                "transforms": ["stars"]
            }
        }
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {
            "key": "cast",
            "extractor": {
                "foreach": "cast[*]",
                "rules": [
                    {"key": "name", "extractor": {"path": "name"}},
                    {"key": "character", "extractor": {"path": "character"}}
                ],
                "transforms": ["stars"]
            }
        }
    ]),
])
def test_scrape_should_transform_subitems(content, skel, rules):
    spec = load_spec(skel | {"rules": rules}, transformers=TRANSFORMERS)
    assert scrape(content, spec) == {
        "cast": [
            "Jack Nicholson as Jack Torrance",
            "Shelley Duvall as Wendy Torrance"
        ]
    }


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {
            "foreach": "//div[@class='info']",
            "key": {"path": "./h3/text()"},
            "extractor": {"path": "./p/text()"}
        }
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {
            "foreach": "info.production[*]",
            "key": {"path": "name"},
            "extractor": {"path": "value"}
        }
    ]),
])
def test_scrape_should_generate_keys_from_content(content, skel, rules):
    spec = load_spec(skel | {"rules": rules})
    assert scrape(content, spec) == {"Country": "United States", "Language": "English"}


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {
            "foreach": "//div[@class='info']",
            "key": {"path": "./h3/text()", "transforms": ["lower"]},
            "extractor": {"path": "./p/text()"}
        }
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {
            "foreach": "info.production[*]",
            "key": {"path": "name", "transforms": ["lower"]},
            "extractor": {"path": "value"}
        }
    ]),
])
def test_scrape_should_transform_generated_key(content, skel, rules):
    spec = load_spec(skel | {"rules": rules}, transformers=TRANSFORMERS)
    assert scrape(content, spec) == {"country": "United States", "language": "English"}


def test_scrape_xml_should_apply_preprocess():
    rules = [{"key": "title", "extractor": {"path": './title/text()'}}]
    pre = ["first_subtree"]
    spec = load_spec(MOVIE_XML_SPEC | {"pre": pre, "rules": rules}, preprocessors=PREPROCESSORS)
    assert scrape(MOVIE_XML, spec) == {"title": "The Shining"}


def test_scrape_json_should_apply_preprocess():
    rules = [{"key": "country", "extractor": {"path": 'production[0].value'}}]
    pre = ["first_submap"]
    spec = load_spec(MOVIE_JSON_SPEC | {"pre": pre, "rules": rules}, preprocessors=PREPROCESSORS)
    assert scrape(MOVIE_JSON, spec) == {"country": "United States"}


def test_scrape_xml_should_apply_multiple_preprocesses():
    rules = [{"key": "title", "extractor": {"path": './text()'}}]
    pre = ["first_subtree", "first_subtree"]
    spec = load_spec(MOVIE_XML_SPEC | {"pre": pre, "rules": rules}, preprocessors=PREPROCESSORS)
    assert scrape(MOVIE_XML, spec) == {"title": "The Shining"}


def test_scrape_json_should_apply_multiple_preprocesses():
    rules = [{"key": "runtime", "extractor": {"path": 'runtime'}}]
    pre = ["first_submap", "first_submap"]
    spec = load_spec(MOVIE_JSON_SPEC | {"pre": pre, "rules": rules}, preprocessors=PREPROCESSORS)
    assert scrape(MOVIE_JSON, spec) == {"runtime": 144}


def test_preprocess_should_produce_compatible_node_for_xml_spec():
    pre = ["empty_map"]
    spec = load_spec(MOVIE_XML_SPEC | {"pre": pre, "rules": []}, preprocessors=PREPROCESSORS)
    with pytest.raises(TypeError):
        _ = scrape(MOVIE_XML, spec)


def test_preprocess_should_produce_compatible_node_for_json_spec():
    pre = ["empty_tree"]
    spec = load_spec(MOVIE_JSON_SPEC | {"pre": pre, "rules": []}, preprocessors=PREPROCESSORS)
    with pytest.raises(TypeError):
        _ = scrape(MOVIE_JSON, spec)


def test_scrape_xml_should_apply_postprocess():
    rules = [{"key": "title", "extractor": {"path": '//title/text()'}}]
    post = ["shorten"]
    spec = load_spec(MOVIE_XML_SPEC | {"rules": rules, "post": post}, postprocessors=POSTPROCESSORS)
    assert scrape(MOVIE_XML, spec) == {"titl": "The Shinin"}


def test_scrape_json_should_apply_postprocess():
    rules = [{"key": "title", "extractor": {"path": 'title'}}]
    post = ["shorten"]
    spec = load_spec(MOVIE_JSON_SPEC | {"rules": rules, "post": post}, postprocessors=POSTPROCESSORS)
    assert scrape(MOVIE_JSON, spec) == {"titl": "The Shinin"}


def test_scrape_xml_should_apply_multiple_postprocesses():
    rules = [{"key": "title", "extractor": {"path": '//title/text()'}}]
    post = ["shorten", "shorten"]
    spec = load_spec(MOVIE_XML_SPEC | {"rules": rules, "post": post}, postprocessors=POSTPROCESSORS)
    assert scrape(MOVIE_XML, spec) == {"tit": "The Shini"}


def test_scrape_json_should_apply_multiple_postprocesses():
    rules = [{"key": "title", "extractor": {"path": 'title'}}]
    post = ["shorten", "shorten"]
    spec = load_spec(MOVIE_JSON_SPEC | {"rules": rules, "post": post}, postprocessors=POSTPROCESSORS)
    assert scrape(MOVIE_JSON, spec) == {"tit": "The Shini"}
