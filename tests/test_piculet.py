import pytest

from pathlib import Path

from piculet import PiculetPath, load_spec, scrape


MOVIE_HTML = Path(__file__).with_name("shining.html").read_text(encoding="utf-8")
MOVIE_JSON = Path(__file__).with_name("shining.json").read_text(encoding="utf-8")


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
    rules = [{"key": "k", "extractor": {"path": "/"}}]
    spec = load_spec({"doctype": "html", "rules": rules})
    assert isinstance(spec.rules[0].extractor.path, PiculetPath)


def test_load_spec_should_load_jmespath():
    rules = [{"key": "k", "extractor": {"path": "p"}}]
    spec = load_spec({"doctype": "json", "rules": rules})
    assert isinstance(spec.rules[0].extractor.path, PiculetPath)


@pytest.mark.parametrize(("content", "doctype"), [
    (MOVIE_HTML, "html"),
    (MOVIE_JSON, "json"),
])
def test_scrape_should_produce_empty_result_for_empty_rules(content, doctype):
    spec = load_spec({"doctype": doctype, "rules": []})
    assert scrape(content, spec) == {}


@pytest.mark.parametrize(("content", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
        {"key": "title", "extractor": {"path": "//title/text()"}}
    ]),
    (MOVIE_JSON, "json", [
        {"key": "title", "extractor": {"path": "title"}}
    ]),
])
def test_scrape_should_produce_scalar_value(content, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules})
    assert scrape(content, spec) == {"title": "The Shining"}


@pytest.mark.parametrize(("content", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
        {"key": "title", "extractor": {"path": "//title/text()"}},
        {"key": "country", "extractor": {"path": "//div[@class='info'][1]/p/text()"}}
    ]),
    (MOVIE_JSON, "json", [
        {"key": "title", "extractor": {"path": "title"}},
        {"key": "country", "extractor": {"path": "info[0].value"}}
    ]),
])
def test_scrape_should_produce_multiple_items_for_multiple_rules(content, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules})
    assert scrape(content, spec) == {"title": "The Shining", "country": "United States"}


@pytest.mark.parametrize(("content", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
        {"key": "title", "extractor": {"path": "//title/text()"}},
        {"key": "foo", "extractor": {"path": "//foo/text()"}}
    ]),
    (MOVIE_JSON, "json", [
        {"key": "title", "extractor": {"path": "title"}},
        {"key": "foo", "extractor": {"path": "foo"}}
    ]),
])
def test_scrape_should_exclude_data_for_rules_with_no_result(content, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules})
    assert scrape(content, spec) == {"title": "The Shining"}


@pytest.mark.parametrize(("content", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
        {"key": "title", "extractor": {"path": "//title/text()", "transforms": ["lower"]}}
    ]),
    (MOVIE_JSON, "json", [
        {"key": "title", "extractor": {"path": "title", "transforms": ["lower"]}}
    ]),
])
def test_scrape_should_transform_result(content, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules}, transformers=TRANSFORMERS)
    assert scrape(content, spec) == {"title": "the shining"}


@pytest.mark.parametrize(("content", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
        {"key": "title", "extractor": {"path": "//title/text()", "transforms": ["remove_spaces", "titlecase"]}}
    ]),
    (MOVIE_JSON, "json", [
        {"key": "title", "extractor": {"path": "title", "transforms": ["remove_spaces", "titlecase"]}}
    ]),
])
def test_scrape_should_apply_transforms_in_order(content, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules}, transformers=TRANSFORMERS)
    assert scrape(content, spec) == {"title": "Theshining"}


@pytest.mark.parametrize(("content", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
        {"key": "genres", "extractor": {"foreach": "//ul[@class='genres']/li", "path": "./text()"}}
    ]),
    (MOVIE_JSON, "json", [
        {"key": "genres", "extractor": {"foreach": "genres[*]", "path": "name"}}
    ]),
])
def test_scrape_should_produce_list_for_multivalued_rule(content, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules})
    assert scrape(content, spec) == {"genres": ["Horror", "Drama"]}


@pytest.mark.parametrize(("content", "doctype", "rules"), [
    (MOVIE_HTML, "html", [
        {"key": "foos", "extractor": {"foreach": "//ul[@class='foos']/li", "path": "./text()"}}
    ]),
    (MOVIE_JSON, "json", [
        {"key": "foos", "extractor": {"foreach": "foos[*]", "path": "text"}}
    ]),
])
def test_scrape_should_exclude_empty_items_in_multivalued_rule_results(content, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules})
    assert scrape(content, spec) == {}


@pytest.mark.parametrize(("content", "doctype", "rules"), [
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
def test_scrape_should_transform_each_value_in_multivalued_result(content, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules}, transformers=TRANSFORMERS)
    assert scrape(content, spec) == {"genres": ["horror", "drama"]}


@pytest.mark.parametrize(("content", "doctype", "rules"), [
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
def test_scrape_should_produce_subitems_for_subrules(content, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules}, transformers=TRANSFORMERS)
    assert scrape(content, spec) == {"director": {"name": "Stanley Kubrick", "id": 1}}


@pytest.mark.parametrize(("content", "doctype", "rules"), [
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
def test_scrape_should_produce_subitem_lists_for_multivalued_subrules(content, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules})
    assert scrape(content, spec) == {
        "cast": [
            {"name": "Jack Nicholson", "character": "Jack Torrance"},
            {"name": "Shelley Duvall", "character": "Wendy Torrance"}
        ]
    }


@pytest.mark.parametrize(("content", "doctype", "rules"), [
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
def test_scrape_should_transform_subitems(content, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules}, transformers=TRANSFORMERS)
    assert scrape(content, spec) == {
        "cast": [
            "Jack Nicholson as Jack Torrance",
            "Shelley Duvall as Wendy Torrance"
        ]
    }


@pytest.mark.parametrize(("content", "doctype", "rules"), [
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
def test_scrape_should_generate_keys_from_content(content, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules})
    assert scrape(content, spec) == {"Country": "United States", "Language": "English"}


@pytest.mark.parametrize(("content", "doctype", "rules"), [
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
def test_scrape_should_transform_generated_key(content, doctype, rules):
    spec = load_spec({"doctype": doctype, "rules": rules}, transformers=TRANSFORMERS)
    assert scrape(content, spec) == {"country": "United States", "language": "English"}


@pytest.mark.parametrize(("content", "doctype", "pre", "rules"), [
    (MOVIE_HTML, "html", ["first_ul"], [
        {"key": "genre", "extractor": {"path": './li[1]/text()'}}
    ]),
    (MOVIE_JSON, "json", ["first_list"], [
        {"key": "genre", "extractor": {"path": '[0].name'}}
    ]),
])
def test_scrape_should_apply_preprocess(content, doctype, pre, rules):
    spec = load_spec({"doctype": doctype, "pre": pre, "rules": rules}, preprocessors=PREPROCESSORS)
    assert scrape(content, spec) == {"genre": "Horror"}


@pytest.mark.parametrize(("content", "doctype", "pre", "rules"), [
    (MOVIE_HTML, "html", ["first_ul", "first_li"], [
        {"key": "genre", "extractor": {"path": './text()'}}
    ]),
    (MOVIE_JSON, "json", ["first_list", "first_map"], [
        {"key": "genre", "extractor": {"path": 'name'}}
    ]),
])
def test_scrape_should_apply_multiple_preprocess(content, doctype, pre, rules):
    spec = load_spec({"doctype": doctype, "pre": pre, "rules": rules}, preprocessors=PREPROCESSORS)
    assert scrape(content, spec) == {"genre": "Horror"}


@pytest.mark.parametrize(("content", "doctype", "post", "rules"), [
    (MOVIE_HTML, "html", ["shorten"], [
        {"key": "title", "extractor": {"path": '//title/text()'}}
    ]),
    (MOVIE_JSON, "json", ["shorten"], [
        {"key": "title", "extractor": {"path": 'title'}}
    ]),
])
def test_scrape_should_apply_postprocess(content, doctype, post, rules):
    spec = load_spec({"doctype": doctype, "rules": rules, "post": post}, postprocessors=POSTPROCESSORS)
    assert scrape(content, spec) == {"titl": "The Shinin"}


@pytest.mark.parametrize(("content", "doctype", "post", "rules"), [
    (MOVIE_HTML, "html", ["shorten", "shorten"], [
        {"key": "title", "extractor": {"path": '//title/text()'}}
    ]),
    (MOVIE_JSON, "json", ["shorten", "shorten"], [
        {"key": "title", "extractor": {"path": 'title'}}
    ]),
])
def test_scrape_should_apply_multiple_postprocesses(content, doctype, post, rules):
    spec = load_spec({"doctype": doctype, "rules": rules, "post": post}, postprocessors=POSTPROCESSORS)
    assert scrape(content, spec) == {"tit": "The Shini"}
