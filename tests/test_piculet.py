import pytest

from pathlib import Path

from piculet import build_tree, load_spec, scrape


MOVIE_HTML_CONTENT = Path(__file__).with_name("shining.html").read_text(encoding="utf-8")
MOVIE_JSON_CONTENT = Path(__file__).with_name("shining.json").read_text(encoding="utf-8")

MOVIE_HTML = build_tree(MOVIE_HTML_CONTENT, doctype="html")
MOVIE_JSON = build_tree(MOVIE_JSON_CONTENT, doctype="json")


TRANSFORMERS = {
    "lower": str.lower,
    "titlecase": str.title,
    "remove_spaces": lambda x: x.replace(" ", ""),
    "id_from_link": lambda x: int(x.split("/")[-1]),
    "stars": lambda x: "%(name)s as %(character)s" % x,
}

PREPROCESSORS = {
    "first_ul": lambda x: x.xpath('./body/ul')[0],
    "first_li": lambda x: x.xpath('./li')[0],
    "first_list": lambda x: [v for v in x.values() if isinstance(v, list)][0],
    "first_map": lambda x: [v for v in x if isinstance(v, dict)][0],
}

POSTPROCESSORS = {
    "shorten": lambda x: {k[:-1]: v[:-1] for k, v in x.items()},
}


def test_load_spec_should_set_preprocessor():
    spec = load_spec({"doctype": "json", "pre": ["first_list"], "rules": []}, preprocessors=PREPROCESSORS)
    assert spec.preprocessors[0]({"x": "X", "ys": ["y1", "y2"], "z": "Z"}) == ["y1", "y2"]


def test_load_spec_should_raise_error_for_unknown_preprocessor():
    with pytest.raises(KeyError):
        _ = load_spec({"doctype": "json", "pre": ["UNKNOWN"], "rules": []}, preprocessors=PREPROCESSORS)


def test_load_spec_should_set_postprocessor():
    spec = load_spec({"doctype": "json", "post": ["shorten"], "rules": []}, postprocessors=POSTPROCESSORS)
    assert spec.postprocessors[0]({"genre": "Horror"}) == {"genr": "Horro"}


def test_load_spec_should_raise_error_for_unknown_postprocessor():
    with pytest.raises(KeyError):
        _ = load_spec({"doctype": "json", "post": ["UNKNOWN"], "rules": []}, postprocessors=POSTPROCESSORS)


def test_load_spec_should_set_transformer():
    rules = [{"key": "k", "extractor": {"path": "p", "transforms": ["lower"]}}]
    spec = load_spec({"doctype": "json", "rules": rules}, transformers=TRANSFORMERS)
    assert spec.rules[0].extractor.transformers[0]("Horror") == "horror"


def test_load_spec_should_raise_error_for_unknown_transformer():
    rules = [{"key": "k", "extractor": {"path": "p", "transforms": ["UNKNOWN"]}}]
    with pytest.raises(KeyError):
        _ = load_spec({"doctype": "json", "rules": rules}, transformers=TRANSFORMERS)


def test_load_spec_should_load_xpath():
    rules = [{"key": "k", "extractor": {"path": "//answer/text()"}}]
    spec = load_spec({"doctype": "html", "rules": rules})
    root = build_tree("<root><answer>42</answer></root>", doctype="html")
    assert spec.rules[0].extractor.path.query(root) == "42"


def test_load_spec_should_load_jmespath():
    rules = [{"key": "k", "extractor": {"path": "root.answer"}}]
    spec = load_spec({"doctype": "json", "rules": rules})
    root = build_tree('{"root": {"answer": "42"}}', doctype="json")
    assert spec.rules[0].extractor.path.query(root) == "42"


@pytest.mark.parametrize(("document", "doctype"), [
    (MOVIE_HTML, "html"),
    (MOVIE_JSON, "json"),
])
def test_scrape_should_produce_empty_result_for_empty_rules(document, doctype):
    spec = load_spec({"doctype": doctype, "rules": []})
    assert scrape(document, spec) == {}


@pytest.mark.parametrize(("document", "doctype", "rules"), [
    (MOVIE_HTML_CONTENT, "html", [
        {"key": "title", "extractor": {"path": "//title/text()"}}
    ]),
    (MOVIE_JSON_CONTENT, "json", [
        {"key": "title", "extractor": {"path": "title"}}
    ]),
])
def test_scrape_should_work_with_str_content(document, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules})
    assert scrape(document, spec) == {"title": "The Shining"}


@pytest.mark.parametrize(("document", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
        {"key": "title", "extractor": {"path": "//title/text()"}}
    ]),
    (MOVIE_JSON, "json", [
        {"key": "title", "extractor": {"path": "title"}}
    ]),
])
def test_scrape_should_produce_scalar_value(document, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules})
    assert scrape(document, spec) == {"title": "The Shining"}


@pytest.mark.parametrize(("document", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
        {"key": "full_title", "extractor": {"path": "//h1//text()"}}
    ]),
])
def test_scrape_xml_should_produce_joined_value(document, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules})
    assert scrape(document, spec) == {"full_title": "The Shining (1980)"}


@pytest.mark.parametrize(("document", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
        {"key": "title", "extractor": {"path": "//title/text()"}},
        {"key": "country", "extractor": {"path": "//div[@class='info'][1]/p/text()"}}
    ]),
    (MOVIE_JSON, "json", [
        {"key": "title", "extractor": {"path": "title"}},
        {"key": "country", "extractor": {"path": "info[0].value"}}
    ]),
])
def test_scrape_should_produce_multiple_items_for_multiple_rules(document, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules})
    assert scrape(document, spec) == {"title": "The Shining", "country": "United States"}


@pytest.mark.parametrize(("document", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
        {"key": "title", "extractor": {"path": "//title/text()"}},
        {"key": "foo", "extractor": {"path": "//foo/text()"}}
    ]),
    (MOVIE_JSON, "json", [
        {"key": "title", "extractor": {"path": "title"}},
        {"key": "foo", "extractor": {"path": "foo"}}
    ]),
])
def test_scrape_should_exclude_data_for_rules_with_no_result(document, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules})
    assert scrape(document, spec) == {"title": "The Shining"}


@pytest.mark.parametrize(("document", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
        {"key": "title", "extractor": {"path": "//title/text()", "transforms": ["lower"]}}
    ]),
    (MOVIE_JSON, "json", [
        {"key": "title", "extractor": {"path": "title", "transforms": ["lower"]}}
    ]),
])
def test_scrape_should_transform_result(document, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules}, transformers=TRANSFORMERS)
    assert scrape(document, spec) == {"title": "the shining"}


@pytest.mark.parametrize(("document", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
        {"key": "title", "extractor": {"path": "//title/text()", "transforms": ["remove_spaces", "titlecase"]}}
    ]),
    (MOVIE_JSON, "json", [
        {"key": "title", "extractor": {"path": "title", "transforms": ["remove_spaces", "titlecase"]}}
    ]),
])
def test_scrape_should_apply_transforms_in_order(document, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules}, transformers=TRANSFORMERS)
    assert scrape(document, spec) == {"title": "Theshining"}


@pytest.mark.parametrize(("document", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
        {"key": "genres", "extractor": {"foreach": "//ul[@class='genres']/li", "path": "./text()"}}
    ]),
    (MOVIE_JSON, "json", [
        {"key": "genres", "extractor": {"foreach": "genres[*]", "path": "name"}}
    ]),
])
def test_scrape_should_produce_list_for_multivalued_rule(document, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules})
    assert scrape(document, spec) == {"genres": ["Horror", "Drama"]}


@pytest.mark.parametrize(("document", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
        {"key": "title", "extractor": {"path": "//title/text()"}},
        {"key": "foos", "extractor": {"foreach": "//ul[@class='foos']/li", "path": "./text()"}}
    ]),
    (MOVIE_JSON, "json", [
        {"key": "title", "extractor": {"path": "title"}},
        {"key": "foos", "extractor": {"foreach": "foos[*]", "path": "text"}}
    ]),
])
def test_scrape_should_exclude_empty_items_in_multivalued_rule_results(document, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules})
    assert scrape(document, spec) == {"title": "The Shining"}


@pytest.mark.parametrize(("document", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
        {
            "key": "genres",
            "extractor": {"foreach": "//ul[@class='genres']/li", "path": "./text()", "transforms": ["lower"]}
        }
    ]),
    (MOVIE_JSON, "json", [
        {
            "key": "genres",
            "extractor": {"foreach": "genres[*]", "path": "name", "transforms": ["lower"]}
        }
    ]),
])
def test_scrape_should_transform_each_value_in_multivalued_result(document, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules}, transformers=TRANSFORMERS)
    assert scrape(document, spec) == {"genres": ["horror", "drama"]}


@pytest.mark.parametrize(("document", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
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
                        "extractor": {"path": "//div[@class='director']//a/@href", "transforms": ["id_from_link"]},
                    }
                ]
            }
        }
    ]),
    (MOVIE_JSON, "json", [
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
def test_scrape_should_produce_subitems_for_subrules(document, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules}, transformers=TRANSFORMERS)
    assert scrape(document, spec) == {"director": {"name": "Stanley Kubrick", "id": 1}}


@pytest.mark.parametrize(("document", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
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
                        "extractor": {"path": "./@href", "transforms": ["id_from_link"]},
                    }
                ]
            }
        }
    ]),
    (MOVIE_JSON, "json", [
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
def test_scrape_should_move_root_for_subitems(document, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules}, transformers=TRANSFORMERS)
    assert scrape(document, spec) == {"director": {"name": "Stanley Kubrick", "id": 1}}


@pytest.mark.parametrize(("document", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
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
    (MOVIE_JSON, "json", [
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
def test_scrape_should_produce_subitem_lists_for_multivalued_subrules(document, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules})
    assert scrape(document, spec) == {
        "cast": [
            {"name": "Jack Nicholson", "character": "Jack Torrance"},
            {"name": "Shelley Duvall", "character": "Wendy Torrance"}
        ]
    }


@pytest.mark.parametrize(("document", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
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
    (MOVIE_JSON, "json", [
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
def test_scrape_root_should_come_before_foreach(document, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules})
    assert scrape(document, spec) == {
        "cast": [
            {"name": "Jack Nicholson", "character": "Jack Torrance"},
            {"name": "Shelley Duvall", "character": "Wendy Torrance"}
        ]
    }


@pytest.mark.parametrize(("document", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
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
    (MOVIE_JSON, "json", [
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
def test_scrape_should_transform_subitems(document, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules}, transformers=TRANSFORMERS)
    assert scrape(document, spec) == {
        "cast": [
            "Jack Nicholson as Jack Torrance",
            "Shelley Duvall as Wendy Torrance"
        ]
    }


@pytest.mark.parametrize(("document", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
        {
            "foreach": "//div[@class='info']",
            "key": {"path": "./h3/text()"},
            "extractor": {"path": "./p/text()"}
        }
    ]),
    (MOVIE_JSON, "json", [
        {
            "foreach": "info[*]",
            "key": {"path": "name"},
            "extractor": {"path": "value"}
        }
    ]),
])
def test_scrape_should_generate_keys_from_document(document, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules})
    assert scrape(document, spec) == {"Country": "United States", "Language": "English"}


@pytest.mark.parametrize(("document", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
        {
            "foreach": "//div[@class='info']",
            "key": {"path": "./h3/text()", "transforms": ["lower"]},
            "extractor": {"path": "./p/text()"}
        }
    ]),
    (MOVIE_JSON, "json", [
        {
            "foreach": "info[*]",
            "key": {"path": "name", "transforms": ["lower"]},
            "extractor": {"path": "value"}
        }
    ]),
])
def test_scrape_should_transform_generated_key(document, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules}, transformers=TRANSFORMERS)
    assert scrape(document, spec) == {"country": "United States", "language": "English"}


@pytest.mark.parametrize(("document", "doctype", "pre", "rules"), [
    (MOVIE_HTML, "html", ["first_ul"], [
        {"key": "genre", "extractor": {"path": './li[1]/text()'}}
    ]),
    (MOVIE_JSON, "json", ["first_list"], [
        {"key": "genre", "extractor": {"path": '[0].name'}}
    ]),
])
def test_scrape_should_apply_preprocess(document, doctype, pre, rules):
    spec = load_spec({"doctype": doctype, "pre": pre, "rules": rules}, preprocessors=PREPROCESSORS)
    assert scrape(document, spec) == {"genre": "Horror"}


@pytest.mark.parametrize(("document", "doctype", "pre", "rules"), [
    (MOVIE_HTML, "html", ["first_ul", "first_li"], [
        {"key": "genre", "extractor": {"path": './text()'}}
    ]),
    (MOVIE_JSON, "json", ["first_list", "first_map"], [
        {"key": "genre", "extractor": {"path": 'name'}}
    ]),
])
def test_scrape_should_apply_multiple_preprocess(document, doctype, pre, rules):
    spec = load_spec({"doctype": doctype, "pre": pre, "rules": rules}, preprocessors=PREPROCESSORS)
    assert scrape(document, spec) == {"genre": "Horror"}


@pytest.mark.parametrize(("document", "doctype", "post", "rules"), [
    (MOVIE_HTML, "html", ["shorten"], [
        {"key": "title", "extractor": {"path": '//title/text()'}}
    ]),
    (MOVIE_JSON, "json", ["shorten"], [
        {"key": "title", "extractor": {"path": 'title'}}
    ]),
])
def test_scrape_should_apply_postprocess(document, doctype, post, rules):
    spec = load_spec({"doctype": doctype, "rules": rules, "post": post}, postprocessors=POSTPROCESSORS)
    assert scrape(document, spec) == {"titl": "The Shinin"}


@pytest.mark.parametrize(("document", "doctype", "post", "rules"), [
    (MOVIE_HTML, "html", ["shorten", "shorten"], [
        {"key": "title", "extractor": {"path": '//title/text()'}}
    ]),
    (MOVIE_JSON, "json", ["shorten", "shorten"], [
        {"key": "title", "extractor": {"path": 'title'}}
    ]),
])
def test_scrape_should_apply_multiple_postprocesses(document, doctype, post, rules):
    spec = load_spec({"doctype": doctype, "rules": rules, "post": post}, postprocessors=POSTPROCESSORS)
    assert scrape(document, spec) == {"tit": "The Shini"}
