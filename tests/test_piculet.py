import pytest

from pathlib import Path

from piculet import build_tree, load_spec, scrape


MOVIE = {
    "html": Path(__file__).with_name("shining.html").read_text(),
    "json": Path(__file__).with_name("shining.json").read_text(),
}

SPEC = {
    "html": {"doctype": "html", "rules": []},
    "json": {"doctype": "json", "rules": []},
}


TRANSFORMERS = {
    "lower": str.lower,
    "titlecase": str.title,
    "remove_spaces": lambda x: x.replace(" ", ""),
    "id_from_link": lambda x: int(x.split("/")[-1]),
    "stars": lambda x: "%(name)s as %(character)s" % x,
}


def shorten_title(root):
    try:
        title_node = root.xpath("//title")[0]
        title_node.text = title_node.text[:-1]
    except AttributeError:
        root["title"] = root["title"][:-1]
    return root


PREPROCESSORS = {
    "shorten_title": shorten_title,
}


POSTPROCESSORS = {
    "shorten_items": lambda x: {k[:-1]: v[:-1] for k, v in x.items()},
}


def test_load_spec_should_set_preprocessor_callable():
    spec = load_spec(SPEC["json"] | {"pre": ["shorten_title"]},
                     preprocessors=PREPROCESSORS)
    root = {"title": "The Shining"}
    assert spec.preprocessors[0](root) == {"title": "The Shinin"}


def test_load_spec_should_raise_error_for_unknown_preprocessor():
    with pytest.raises(KeyError):
        _ = load_spec(SPEC["json"] | {"pre": ["UNKNOWN"]},
                      preprocessors=PREPROCESSORS)


def test_load_spec_should_set_postprocessor_callable():
    spec = load_spec(SPEC["json"] | {"post": ["shorten_items"]},
                     postprocessors=POSTPROCESSORS)
    data = {"genre": "Horror"}
    assert spec.postprocessors[0](data) == {"genr": "Horro"}


def test_load_spec_should_raise_error_for_unknown_postprocessor():
    with pytest.raises(KeyError):
        _ = load_spec(SPEC["json"] | {"post": ["UNKNOWN"]},
                      postprocessors=POSTPROCESSORS)


def test_load_spec_should_set_transformer_callable():
    rules = [{"key": "k", "extractor": {"path": "p", "transforms": ["lower"]}}]
    spec = load_spec(SPEC["json"] | {"rules": rules}, transformers=TRANSFORMERS)
    assert spec.rules[0].extractor.transformers[0]("Horror") == "horror"


def test_load_spec_should_raise_error_for_unknown_transformer():
    rules = [{"key": "k", "extractor": {"path": "p", "transforms": ["UNKNOWN"]}}]
    with pytest.raises(KeyError):
        _ = load_spec(SPEC["json"] | {"rules": rules}, transformers=TRANSFORMERS)


def test_load_spec_should_load_xpath():
    rules = [{"key": "title", "extractor": {"path": "//title/text()"}}]
    spec = load_spec(SPEC["html"] | {"rules": rules})
    root = build_tree("<html><head><title>The Shining</title></head></html>", doctype="html")
    assert spec.rules[0].extractor.path.query(root) == "The Shining"


def test_load_spec_should_load_jmespath():
    rules = [{"key": "title", "extractor": {"path": "title"}}]
    spec = load_spec(SPEC["json"] | {"rules": rules})
    root = build_tree('{"title": "The Shining"}', doctype="json")
    assert spec.rules[0].extractor.path.query(root) == "The Shining"


@pytest.mark.parametrize(("doctype",), [
    ("html",),
    ("json",),
])
def test_scrape_should_produce_empty_result_for_empty_rules(doctype):
    spec = load_spec(SPEC[doctype] | {"rules": []})
    assert scrape(MOVIE[doctype], spec) == {}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {"key": "title", "extractor": {"path": "//title/text()"}}
    ]),
    ("json", [
        {"key": "title", "extractor": {"path": "title"}}
    ]),
])
def test_scrape_should_produce_scalar_value(doctype, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules})
    assert scrape(MOVIE[doctype], spec) == {"title": "The Shining"}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {"key": "full_title", "extractor": {"path": "//h1//text()"}}
    ]),
])
def test_scrape_xpath_should_produce_joined_text(doctype, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules})
    assert scrape(MOVIE[doctype], spec) == {"full_title": "The Shining (1980)"}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {"key": "title", "extractor": {"path": "//title/text()"}},
        {"key": "country", "extractor": {"path": "//div[@class='info'][1]/p/text()"}}
    ]),
    ("json", [
        {"key": "title", "extractor": {"path": "title"}},
        {"key": "country", "extractor": {"path": "info[0].value"}}
    ]),
])
def test_scrape_should_produce_multiple_items_for_multiple_rules(doctype, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules})
    assert scrape(MOVIE[doctype], spec) == {"title": "The Shining", "country": "United States"}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {"key": "title", "extractor": {"path": "//title/text()"}},
        {"key": "foo", "extractor": {"path": "//foo/text()"}}
    ]),
    ("json", [
        {"key": "title", "extractor": {"path": "title"}},
        {"key": "foo", "extractor": {"path": "foo"}}
    ]),
])
def test_scrape_should_exclude_data_for_rules_with_no_result(doctype, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules})
    assert scrape(MOVIE[doctype], spec) == {"title": "The Shining"}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {"key": "title", "extractor": {"path": "//title/text()",
                                       "transforms": ["lower"]}}
    ]),
    ("json", [
        {"key": "title", "extractor": {"path": "title",
                                       "transforms": ["lower"]}}
    ]),
])
def test_scrape_should_transform_result(doctype, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules}, transformers=TRANSFORMERS)
    assert scrape(MOVIE[doctype], spec) == {"title": "the shining"}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {"key": "title", "extractor": {"path": "//title/text()",
                                       "transforms": ["remove_spaces", "titlecase"]}}
    ]),
    ("json", [
        {"key": "title", "extractor": {"path": "title",
                                       "transforms": ["remove_spaces", "titlecase"]}}
    ]),
])
def test_scrape_should_apply_transforms_in_order(doctype, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules}, transformers=TRANSFORMERS)
    assert scrape(MOVIE[doctype], spec) == {"title": "Theshining"}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {"key": "genres", "extractor": {"foreach": "//ul[@class='genres']/li",
                                        "path": "./text()"}}
    ]),
    ("json", [
        {"key": "genres", "extractor": {"foreach": "genres[*]",
                                        "path": "name"}}
    ]),
])
def test_scrape_should_produce_list_for_multivalued_rule(doctype, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules})
    assert scrape(MOVIE[doctype], spec) == {"genres": ["Horror", "Drama"]}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {"key": "title", "extractor": {"path": "//title/text()"}},
        {"key": "foos", "extractor": {"foreach": "//ul[@class='foos']/li",
                                      "path": "./text()"}}
    ]),
    ("json", [
        {"key": "title", "extractor": {"path": "title"}},
        {"key": "foos", "extractor": {"foreach": "foos[*]",
                                      "path": "text"}}
    ]),
])
def test_scrape_should_exclude_empty_items_in_multivalued_rule_results(doctype, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules})
    assert scrape(MOVIE[doctype], spec) == {"title": "The Shining"}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {
            "key": "genres",
            "extractor": {"foreach": "//ul[@class='genres']/li",
                          "path": "./text()",
                          "transforms": ["lower"]}
        }
    ]),
    ("json", [
        {
            "key": "genres",
            "extractor": {"foreach": "genres[*]",
                          "path": "name",
                          "transforms": ["lower"]}
        }
    ]),
])
def test_scrape_should_transform_each_value_in_multivalued_result(doctype, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules}, transformers=TRANSFORMERS)
    assert scrape(MOVIE[doctype], spec) == {"genres": ["horror", "drama"]}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
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
                        "extractor": {"path": "//div[@class='director']//a/@href",
                                      "transforms": ["id_from_link"]},
                    }
                ]
            }
        }
    ]),
    ("json", [
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
def test_scrape_should_produce_subitems_for_subrules(doctype, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules}, transformers=TRANSFORMERS)
    assert scrape(MOVIE[doctype], spec) == {"director": {"name": "Stanley Kubrick", "id": 1}}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {
            "key": "director",
            "extractor": {
                "root": "//div[@class='director']//a",
                "rules": [
                    {
                        "key": "name",
                        "extractor": {"path": "./text()"}
                    },
                    {
                        "key": "id",
                        "extractor": {"path": "./@href",
                                      "transforms": ["id_from_link"]},
                    }
                ]
            }
        }
    ]),
    ("json", [
        {
            "key": "director",
            "extractor": {
                "root": "director",
                "rules": [
                    {"key": "name", "extractor": {"path": "name"}},
                    {"key": "id", "extractor": {"path": "id"}}
                ]
            }
        }
    ]),
])
def test_scrape_should_move_root_for_subitems(doctype, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules}, transformers=TRANSFORMERS)
    assert scrape(MOVIE[doctype], spec) == {"director": {"name": "Stanley Kubrick", "id": 1}}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
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
    ("json", [
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
def test_scrape_should_produce_subitem_lists_for_multivalued_subrules(doctype, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules})
    assert scrape(MOVIE[doctype], spec) == {
        "cast": [
            {"name": "Jack Nicholson", "character": "Jack Torrance"},
            {"name": "Shelley Duvall", "character": "Wendy Torrance"}
        ]
    }


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {
            "key": "cast",
            "extractor": {
                "root": "//table[@class='cast']",
                "foreach": "./tr",
                "rules": [
                    {"key": "name", "extractor": {"path": "./td[1]/a/text()"}},
                    {"key": "character", "extractor": {"path": "./td[2]/text()"}}
                ]
            }
        }
    ]),
    ("json", [
        {
            "key": "cast",
            "extractor": {
                "root": "cast",
                "foreach": "[*]",
                "rules": [
                    {"key": "name", "extractor": {"path": "name"}},
                    {"key": "character", "extractor": {"path": "character"}}
                ]
            }
        }
    ]),
])
def test_scrape_root_should_come_before_foreach(doctype, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules})
    assert scrape(MOVIE[doctype], spec) == {
        "cast": [
            {"name": "Jack Nicholson", "character": "Jack Torrance"},
            {"name": "Shelley Duvall", "character": "Wendy Torrance"}
        ]
    }


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
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
    ("json", [
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
def test_scrape_should_transform_subitems(doctype, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules}, transformers=TRANSFORMERS)
    assert scrape(MOVIE[doctype], spec) == {
        "cast": [
            "Jack Nicholson as Jack Torrance",
            "Shelley Duvall as Wendy Torrance"
        ]
    }


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {
            "foreach": "//div[@class='info']",
            "key": {"path": "./h3/text()"},
            "extractor": {"path": "./p/text()"}
        }
    ]),
    ("json", [
        {
            "foreach": "info[*]",
            "key": {"path": "name"},
            "extractor": {"path": "value"}
        }
    ]),
])
def test_scrape_should_generate_keys_from_document(doctype, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules})
    assert scrape(MOVIE[doctype], spec) == {"Country": "United States", "Language": "English"}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {
            "foreach": "//div[@class='info']",
            "key": {"path": "./h3/text()", "transforms": ["lower"]},
            "extractor": {"path": "./p/text()"}
        }
    ]),
    ("json", [
        {
            "foreach": "info[*]",
            "key": {"path": "name", "transforms": ["lower"]},
            "extractor": {"path": "value"}
        }
    ]),
])
def test_scrape_should_transform_generated_key(doctype, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules}, transformers=TRANSFORMERS)
    assert scrape(MOVIE[doctype], spec) == {"country": "United States", "language": "English"}


@pytest.mark.parametrize(("doctype", "pre", "rules"), [
    ("html", ["shorten_title"], [
        {"key": "title", "extractor": {"path": "//title/text()"}}
    ]),
    ("json", ["shorten_title"], [
        {"key": "title", "extractor": {"path": "title"}}
    ]),
])
def test_scrape_should_apply_preprocess(doctype, pre, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules, "pre": pre},
                     preprocessors=PREPROCESSORS)
    assert scrape(MOVIE[doctype], spec) == {"title": "The Shinin"}


@pytest.mark.parametrize(("doctype", "pre", "rules"), [
    ("html", ["shorten_title", "shorten_title"], [
        {"key": "title", "extractor": {"path": "//title/text()"}}
    ]),
    ("json", ["shorten_title", "shorten_title"], [
        {"key": "title", "extractor": {"path": 'title'}}
    ]),
])
def test_scrape_should_apply_multiple_preprocesses(doctype, pre, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules, "pre": pre},
                     preprocessors=PREPROCESSORS)
    assert scrape(MOVIE[doctype], spec) == {"title": "The Shini"}


@pytest.mark.parametrize(("doctype", "post", "rules"), [
    ("html", ["shorten_items"], [
        {"key": "title", "extractor": {"path": "//title/text()"}}
    ]),
    ("json", ["shorten_items"], [
        {"key": "title", "extractor": {"path": "title"}}
    ]),
])
def test_scrape_should_apply_postprocess(doctype, post, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules, "post": post},
                     postprocessors=POSTPROCESSORS)
    assert scrape(MOVIE[doctype], spec) == {"titl": "The Shinin"}


@pytest.mark.parametrize(("doctype", "post", "rules"), [
    ("html", ["shorten_items", "shorten_items"], [
        {"key": "title", "extractor": {"path": "//title/text()"}}
    ]),
    ("json", ["shorten_items", "shorten_items"], [
        {"key": "title", "extractor": {"path": "title"}}
    ]),
])
def test_scrape_should_apply_multiple_postprocesses(doctype, post, rules):
    spec = load_spec(SPEC[doctype] | {"rules": rules, "post": post},
                     postprocessors=POSTPROCESSORS)
    assert scrape(MOVIE[doctype], spec) == {"tit": "The Shini"}
