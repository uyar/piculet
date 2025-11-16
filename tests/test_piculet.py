import pytest

import json
from pathlib import Path

import piculet


MOVIE_XML_SPEC_FILE = Path(__file__).parent / "movie_xml_spec.json"
MOVIE_XML_SPEC = json.loads(MOVIE_XML_SPEC_FILE.read_text(encoding="utf-8"))
MOVIE_XML = Path(__file__).with_name("shining.html").read_text(encoding="utf-8")

MOVIE_JSON_SPEC_FILE = Path(__file__).with_name("movie_json_spec.json")
MOVIE_JSON_SPEC = json.loads(MOVIE_JSON_SPEC_FILE.read_text(encoding="utf-8"))
MOVIE_JSON = Path(__file__).with_name("shining.json").read_text(encoding="utf-8")


piculet.preprocessors.update({
    "nothing": lambda x: x,
    "first_subtree": lambda x: x.xpath('./*[1]')[0],  # type: ignore
    "first_submap": lambda x: x.get("info", {}),  # type: ignore
    "empty_tree": lambda _: piculet._PARSERS["xml"]("<root/>"),
    "empty_map": lambda _: {},
})

piculet.postprocessors.update({
    "nothing": lambda x: x,
    "shorten": lambda x: {k[:-1]: v[:-1] for k, v in x.items()},
})


def test_load_spec_should_load_preprocess_from_str():
    spec = piculet.load_spec(MOVIE_XML_SPEC | {"pre": ["nothing"], "rules": []})
    assert isinstance(spec.pre[0], piculet.Preprocess)


def test_dump_spec_should_dump_preprocess_as_str():
    spec = piculet.load_spec(MOVIE_XML_SPEC | {"pre": ["nothing"], "rules": []})
    assert piculet.dump_spec(spec)["pre"][0] == "nothing"


def test_load_spec_should_raise_error_for_unknown_preprocess():
    with pytest.raises(ValueError):
        _ = piculet.load_spec(MOVIE_XML_SPEC | {"pre": ["UNKNOWN"], "rules": []})


def test_load_spec_should_load_postprocess_from_str():
    spec = piculet.load_spec(MOVIE_XML_SPEC | {"post": ["nothing"], "rules": []})
    assert isinstance(spec.post[0], piculet.Postprocess)


def test_dump_spec_should_dump_postprocess_as_str():
    spec = piculet.load_spec(MOVIE_XML_SPEC | {"post": ["nothing"], "rules": []})
    assert piculet.dump_spec(spec)["post"][0] == "nothing"


def test_load_spec_should_raise_error_for_unknown_postprocess():
    with pytest.raises(ValueError):
        _ = piculet.load_spec(MOVIE_XML_SPEC | {"post": ["UNKNOWN"], "rules": []})


def test_load_spec_should_load_transform_from_str():
    rules = [{"key": "k", "extractor": {"path": "/", "transforms": ["strip"]}}]
    spec = piculet.load_spec(MOVIE_XML_SPEC | {"rules": rules})
    assert isinstance(spec.rules[0].extractor.transforms[0], piculet.Transform)


def test_dump_spec_should_dump_transform_as_str():
    rules = [{"key": "k", "extractor": {"path": "/", "transforms": ["strip"]}}]
    spec = piculet.load_spec(MOVIE_XML_SPEC | {"rules": rules})
    assert piculet.dump_spec(spec)["rules"][0]["extractor"]["transforms"][0] == "strip"


def test_load_spec_should_raise_error_for_unknown_transform():
    rules = [{"key": "k", "extractor": {"path": "/", "transforms": ["UNKNOWN"]}}]
    with pytest.raises(ValueError):
        _ = piculet.load_spec(MOVIE_XML_SPEC | {"rules": rules})


def test_load_spec_should_load_xml_path_from_str():
    rules = [{"key": "k", "extractor": {"path": "/"}}]
    spec = piculet.load_spec(MOVIE_XML_SPEC | {"rules": rules})
    assert isinstance(spec.rules[0].extractor.path, piculet.XMLPath)


def test_dump_spec_should_dump_xml_path_as_str():
    rules = [{"key": "k", "extractor": {"path": "/"}}]
    spec = piculet.load_spec(MOVIE_XML_SPEC | {"rules": rules})
    assert piculet.dump_spec(spec)["rules"][0]["extractor"]["path"] == "/"


def test_load_spec_should_load_json_path_from_str():
    rules = [{"key": "k", "extractor": {"path": "p"}}]
    spec = piculet.load_spec(MOVIE_JSON_SPEC | {"rules": rules})
    assert isinstance(spec.rules[0].extractor.path, piculet.JSONPath)


def test_dump_spec_should_dump_json_path_as_str():
    rules = [{"key": "k", "extractor": {"path": "p"}}]
    spec = piculet.load_spec(MOVIE_JSON_SPEC | {"rules": rules})
    assert piculet.dump_spec(spec)["rules"][0]["extractor"]["path"] == "p"


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, []),
    (MOVIE_JSON, MOVIE_JSON_SPEC, []),
])
def test_scrape_should_produce_empty_result_for_empty_rules(content, skel, rules):
    spec = piculet.load_spec(skel | {"rules": rules})
    assert piculet.scrape(content, spec) == {}


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {"key": "title", "extractor": {"path": "//title/text()"}}
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {"key": "title", "extractor": {"path": "title"}}
    ]),
])
def test_scrape_should_produce_scalar_text(content, skel, rules):
    spec = piculet.load_spec(skel | {"rules": rules})
    assert piculet.scrape(content, spec) == {"title": "The Shining"}


def test_scrape_xml_should_support_string_join():
    rules = [{"key": "full_title", "extractor": {"path": "string-join(//h1//text(), '')"}}]
    spec = piculet.load_spec(MOVIE_XML_SPEC | {"rules": rules})
    assert piculet.scrape(MOVIE_XML, spec) == {"full_title": "The Shining (1980)"}


def test_scrape_xml_should_support_string_join_using_given_separator():
    rules = [
        {
            "key": "cast_names",
            "extractor": {"path": "string-join(//table[@class='cast']/tr/td[1]/a/text(), ', ')"}
        }
    ]
    spec = piculet.load_spec(MOVIE_XML_SPEC | {"rules": rules})
    assert piculet.scrape(MOVIE_XML, spec) == {"cast_names": "Jack Nicholson, Shelley Duvall"}


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {"key": "title", "extractor": {"path": "//title/text()"}},
        {"key": "year", "extractor": {"path": "//span[@class='year']/text()", "transforms": ["int"]}}
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {"key": "title", "extractor": {"path": "title"}},
        {"key": "year", "extractor": {"path": "year"}}
    ]),
])
def test_scrape_should_produce_multiple_items_for_multiple_rules(content, skel, rules):
    spec = piculet.load_spec(skel | {"rules": rules})
    assert piculet.scrape(content, spec) == {"title": "The Shining", "year": 1980}


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
    spec = piculet.load_spec(skel | {"rules": rules})
    assert piculet.scrape(content, spec) == {"title": "The Shining"}


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {"key": "title", "extractor": {"path": "//title/text()"}, "transforms": ["lower"]}
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {"key": "title", "extractor": {"path": "title"}, "transforms": ["lower"]}
    ]),
])
def test_scrape_should_transform_result(content, skel, rules):
    spec = piculet.load_spec(skel | {"rules": rules})
    assert piculet.scrape(content, spec) == {"title": "the shining"}


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {"key": "title", "extractor": {"path": "//title/text()"}, "transforms": ["underscore"]}
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {"key": "title", "extractor": {"path": "title"}, "transforms": ["underscore"]}
    ]),
])
def test_scrape_should_accept_registered_transform(content, skel, rules):
    piculet.transformers["underscore"] = lambda s: s.replace(" ", "_")
    spec = piculet.load_spec(skel | {"rules": rules})
    assert piculet.scrape(content, spec) == {"title": "The_Shining"}
    del piculet.transformers["underscore"]


def test_scrape_xml_should_apply_transforms_in_order():
    piculet.transformers["removepeople"] = lambda s: s.removeprefix("/people/")
    rules = [
        {
            "key": "directorid",
            "extractor": {"path": "//div[@class='director']//a/@href"},
            "transforms": ["removepeople", "int"]
        }
    ]
    spec = piculet.load_spec(MOVIE_XML_SPEC | {"rules": rules})
    assert piculet.scrape(MOVIE_XML, spec) == {"directorid": 1}
    del piculet.transformers["removepeople"]


def test_scrape_json_should_apply_transforms_in_order():
    piculet.transformers["titlecase"] = str.title
    piculet.transformers["removespaces"] = lambda s: s.replace(" ", "")
    rules = [
        {
            "key": "title",
            "extractor": {"path": "title"},
            "transforms": ["removespaces", "titlecase"]
        }
    ]
    spec = piculet.load_spec(MOVIE_JSON_SPEC | {"rules": rules})
    assert piculet.scrape(MOVIE_JSON, spec) == {"title": "Theshining"}
    del piculet.transformers["removespaces"]
    del piculet.transformers["titlecase"]


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {
            "key": "genres",
            "extractor": {
                "foreach": "//ul[@class='genres']/li",
                "path": "./text()"
            }
        }
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {
            "key": "genres",
            "extractor": {
                "foreach": "genres[*]",
                "path": "name"
            }
        }
    ]),
])
def test_scrape_should_produce_list_for_multivalued_rule(content, skel, rules):
    spec = piculet.load_spec(skel | {"rules": rules})
    assert piculet.scrape(content, spec) == {"genres": ["Horror", "Drama"]}


@pytest.mark.parametrize(("content", "skel", "rules"), [
    (MOVIE_XML, MOVIE_XML_SPEC, [
        {
            "key": "foos",
            "extractor": {
                "foreach": "//ul[@class='foos']/li",
                "path": "./text()"
            }
        }
    ]),
    (MOVIE_JSON, MOVIE_JSON_SPEC, [
        {
            "key": "foos",
            "extractor": {
                "foreach": "foos[*]",
                "path": "text"
            }
        }
    ]),
])
def test_scrape_should_exclude_empty_items_in_multivalued_rule_results(content, skel, rules):
    spec = piculet.load_spec(skel | {"rules": rules})
    assert piculet.scrape(content, spec) == {}


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
    spec = piculet.load_spec(skel | {"rules": rules})
    assert piculet.scrape(content, spec) == {"genres": ["horror", "drama"]}


def test_scrape_xml_should_produce_subitems_for_subrules():
    rules = [
        {
            "key": "director",
            "extractor": {
                "rules": [
                    {
                        "key": "name",
                        "extractor": {"path": "//div[@class='director']//a/text()"}
                    },
                    {
                        "key": "link",
                        "extractor": {"path": "//div[@class='director']//a/@href"}
                    }
                ]
            }
        }
    ]
    spec = piculet.load_spec(MOVIE_XML_SPEC | {"rules": rules})
    assert piculet.scrape(MOVIE_XML, spec) == {"director": {"name": "Stanley Kubrick", "link": "/people/1"}}


def test_scrape_json_should_produce_subitems_for_subrules():
    rules = [
        {
            "key": "director",
            "extractor": {
                "rules": [
                    {"key": "name", "extractor": {"path": "director.name"}},
                    {"key": "id", "extractor": {"path": "director.id"}}
                ]
            }
        }
    ]
    spec = piculet.load_spec(MOVIE_JSON_SPEC | {"rules": rules})
    assert piculet.scrape(MOVIE_JSON, spec) == {"director": {"name": "Stanley Kubrick", "id": 1}}


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
    spec = piculet.load_spec(skel | {"rules": rules})
    assert piculet.scrape(content, spec) == {
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
    piculet.transformers["stars"] = lambda x: "%(name)s as %(character)s" % x
    spec = piculet.load_spec(skel | {"rules": rules})
    assert piculet.scrape(content, spec) == {
        "cast": [
            "Jack Nicholson as Jack Torrance",
            "Shelley Duvall as Wendy Torrance"
        ]
    }
    del piculet.transformers["stars"]


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
    spec = piculet.load_spec(skel | {"rules": rules})
    assert piculet.scrape(content, spec) == {"Country": "United States", "Language": "English"}


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
    spec = piculet.load_spec(skel | {"rules": rules})
    assert piculet.scrape(content, spec) == {"country": "United States", "language": "English"}


def test_scrape_xml_should_apply_preprocess():
    rules = [{"key": "title", "extractor": {"path": './title/text()'}}]
    pre = ["first_subtree"]
    spec = piculet.load_spec(MOVIE_XML_SPEC | {"pre": pre, "rules": rules})
    data = piculet.scrape(MOVIE_XML, spec)
    assert data == {"title": "The Shining"}


def test_scrape_json_should_apply_preprocess():
    rules = [{"key": "country", "extractor": {"path": 'production[0].value'}}]
    pre = ["first_submap"]
    spec = piculet.load_spec(MOVIE_JSON_SPEC | {"pre": pre, "rules": rules})
    data = piculet.scrape(MOVIE_JSON, spec)
    assert data == {"country": "United States"}


def test_scrape_xml_should_apply_multiple_preprocesses():
    rules = [{"key": "title", "extractor": {"path": './text()'}}]
    pre = ["first_subtree", "first_subtree"]
    spec = piculet.load_spec(MOVIE_XML_SPEC | {"pre": pre, "rules": rules})
    data = piculet.scrape(MOVIE_XML, spec)
    assert data == {"title": "The Shining"}


def test_preprocess_should_produce_compatible_node_for_xml_spec():
    pre = ["empty_map"]
    spec = piculet.load_spec(MOVIE_XML_SPEC | {"pre": pre, "rules": []})
    with pytest.raises(TypeError):
        _ = piculet.scrape(MOVIE_XML, spec)


def test_preprocess_should_produce_compatible_node_for_json_spec():
    pre = ["empty_tree"]
    spec = piculet.load_spec(MOVIE_JSON_SPEC | {"pre": pre, "rules": []})
    with pytest.raises(TypeError):
        _ = piculet.scrape(MOVIE_JSON, spec)


def test_scrape_json_should_apply_multiple_preprocesses():
    rules = [{"key": "runtime", "extractor": {"path": 'runtime'}}]
    pre = ["first_submap", "first_submap"]
    spec = piculet.load_spec(MOVIE_JSON_SPEC | {"pre": pre, "rules": rules})
    data = piculet.scrape(MOVIE_JSON, spec)
    assert data == {"runtime": 144}


def test_scrape_xml_should_apply_postprocess():
    rules = [{"key": "title", "extractor": {"path": '//title/text()'}}]
    post = ["shorten"]
    spec = piculet.load_spec(MOVIE_XML_SPEC | {"rules": rules, "post": post})
    data = piculet.scrape(MOVIE_XML, spec)
    assert data == {"titl": "The Shinin"}


def test_scrape_json_should_apply_postprocess():
    rules = [{"key": "title", "extractor": {"path": 'title'}}]
    post = ["shorten"]
    spec = piculet.load_spec(MOVIE_JSON_SPEC | {"rules": rules, "post": post})
    data = piculet.scrape(MOVIE_JSON, spec)
    assert data == {"titl": "The Shinin"}


def test_scrape_xml_should_apply_multiple_postprocesses():
    rules = [{"key": "title", "extractor": {"path": '//title/text()'}}]
    post = ["shorten", "shorten"]
    spec = piculet.load_spec(MOVIE_XML_SPEC | {"rules": rules, "post": post})
    data = piculet.scrape(MOVIE_XML, spec)
    assert data == {"tit": "The Shini"}


def test_scrape_json_should_apply_multiple_postprocesses():
    rules = [{"key": "title", "extractor": {"path": 'title'}}]
    post = ["shorten", "shorten"]
    spec = piculet.load_spec(MOVIE_JSON_SPEC | {"rules": rules, "post": post})
    data = piculet.scrape(MOVIE_JSON, spec)
    assert data == {"tit": "The Shini"}
