import pytest

from pathlib import Path
from typing import Any, TypeAlias

from piculet import (
    DocType,
    Node,
    Picker,
    Postprocessor,
    Preprocessor,
    Transformer,
    XMLNode,
    build_tree,
    dump_spec,
    load_spec,
)


MOVIE: dict[DocType, str] = {
    "html": Path(__file__).with_name("shining.html").read_text(),
    "json": Path(__file__).with_name("shining.json").read_text(),
}


TRANSFORMERS: dict[str, Transformer] = {
    "lower": str.lower,
    "titlecase": str.title,
    "remove_spaces": lambda x: x.replace(" ", ""),
    "id_from_link": lambda x: int(x.split("/")[-1]),
    "stars": lambda x: "%(name)s as %(character)s" % x,
}


def shorten_title(root: Node) -> Node:
    match root:
        case XMLNode():
            title_nodes: list[XMLNode] = root.xpath("//title")  # type: ignore
            title = title_nodes[0].text
            assert title is not None
            title_nodes[0].text = title[:-1]
        case _:
            root["title"] = root["title"][:-1]
    return root


PREPROCESSORS: dict[str, Preprocessor] = {
    "shorten_title": shorten_title,
}


POSTPROCESSORS: dict[str, Postprocessor] = {
    "shorten_items": lambda x: {k[:-1]: v[:-1] for k, v in x.items()},
}


def test_load_spec_should_set_preprocessor_callable() -> None:
    spec = load_spec({"rules": [], "pre": ["shorten_title"]}, preprocessors=PREPROCESSORS)
    assert spec._pre[0]({"title": "The Shining"}) == {"title": "The Shinin"}


def test_load_spec_should_raise_error_for_unknown_preprocessor() -> None:
    with pytest.raises(KeyError):
        _ = load_spec({"rules": [], "pre": ["UNKNOWN"]}, preprocessors=PREPROCESSORS)


def test_load_spec_should_set_postprocessor_callable() -> None:
    spec = load_spec({"rules": [], "post": ["shorten_items"]}, postprocessors=POSTPROCESSORS)
    assert spec._post[0]({"genre": "Horror"}) == {"genr": "Horro"}


def test_load_spec_should_raise_error_for_unknown_postprocessor() -> None:
    with pytest.raises(KeyError):
        _ = load_spec({"rules": [], "post": ["UNKNOWN"]}, postprocessors=POSTPROCESSORS)


def test_load_spec_should_set_transformer_callable() -> None:
    rules = [{"key": "k", "extractor": {"path": "p", "transforms": ["lower"]}}]
    spec = load_spec({"rules": rules}, transformers=TRANSFORMERS)
    assert spec.rules[0].extractor._transforms[0]("Horror") == "horror"


def test_load_spec_should_raise_error_for_unknown_transformer() -> None:
    rules = [{"key": "k", "extractor": {"path": "p", "transforms": ["UNKNOWN"]}}]
    with pytest.raises(KeyError):
        _ = load_spec({"rules": rules}, transformers=TRANSFORMERS)


def test_load_spec_should_load_xpath() -> None:
    rules = [{"key": "title", "extractor": {"path": "//title/text()"}}]
    spec = load_spec({"rules": rules})
    root = build_tree('<html><head><title>The Shining</title></head></html>', doctype="html")
    extractor = spec.rules[0].extractor
    assert isinstance(extractor, Picker) and (extractor.path.apply(root) == "The Shining")


def test_dump_spec_should_dump_xpath_as_str() -> None:
    rules = [{"key": "title", "extractor": {"path": "//title/text()"}}]
    spec = load_spec({"rules": rules})
    assert dump_spec(spec) == {"rules": rules}


def test_load_spec_should_load_jmespath() -> None:
    rules = [{"key": "title", "extractor": {"path": "title"}}]
    spec = load_spec({"rules": rules})
    root = build_tree('{"title": "The Shining"}', doctype="json")
    extractor = spec.rules[0].extractor
    assert isinstance(extractor, Picker) and (extractor.path.apply(root) == "The Shining")


def test_dump_spec_json_should_dump_jmespath_as_str() -> None:
    rules = [{"key": "title", "extractor": {"path": "//title/text()"}}]
    spec = load_spec({"rules": rules})
    assert dump_spec(spec) == {"rules": rules}


Rule: TypeAlias = dict[str, Any]


@pytest.mark.parametrize("doctype", ["html", "json"])
def test_scrape_should_produce_empty_result_for_empty_rules(doctype: DocType) -> None:
    spec = load_spec({"rules": []})
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {"key": "title", "extractor": {"path": "//title/text()"}},
    ]),
    ("json", [
        {"key": "title", "extractor": {"path": "title"}},
    ]),
])
def test_scrape_should_produce_scalar(
    doctype: DocType,
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules})
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {"title": "The Shining"}


def test_scrape_xpath_should_produce_joined_text() -> None:
    rules = [{"key": "full_title", "extractor": {"path": "//h1//text()"}}]
    spec = load_spec({"rules": rules})
    assert spec.scrape(MOVIE["html"], doctype="html") == {"full_title": "The Shining (1980)"}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {"key": "title", "extractor": {"path": "//title/text()"}},
        {"key": "country", "extractor": {"path": "//div[@class='info'][1]/p/text()"}},
    ]),
    ("json", [
        {"key": "title", "extractor": {"path": "title"}},
        {"key": "country", "extractor": {"path": "info[0].value"}},
    ]),
])
def test_scrape_should_produce_multiple_items_for_multiple_rules(
    doctype: DocType,
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules})
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {
        "title": "The Shining",
        "country": "United States",
    }


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {"key": "title", "extractor": {"path": "//title/text()"}},
        {"key": "foo", "extractor": {"path": "//foo/text()"}},
    ]),
    ("json", [
        {"key": "title", "extractor": {"path": "title"}},
        {"key": "foo", "extractor": {"path": "foo"}},
    ]),
])
def test_scrape_should_exclude_data_for_rules_with_no_result(
    doctype: DocType,
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules})
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {"title": "The Shining"}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {"key": "title", "extractor": {"path": "//title/text()", "transforms": ["lower"]}},
    ]),
    ("json", [
        {"key": "title", "extractor": {"path": "title", "transforms": ["lower"]}},
    ]),
])
def test_scrape_should_transform_result(
    doctype: DocType,
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules}, transformers=TRANSFORMERS)
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {"title": "the shining"}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {
            "key": "title", "extractor": {
                "path": "//title/text()",
                "transforms": ["remove_spaces", "titlecase"],
            },
        },
    ]),
    ("json", [
        {
            "key": "title",
            "extractor": {
                "path": "title",
                "transforms": ["remove_spaces", "titlecase"],
            },
        },
    ]),
])
def test_scrape_should_apply_transforms_in_order(
    doctype: DocType,
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules}, transformers=TRANSFORMERS)
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {"title": "Theshining"}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {
            "key": "genres",
            "extractor": {"foreach": "//ul[@class='genres']/li", "path": "./text()"},
        },
    ]),
    ("json", [
        {
            "key": "genres",
            "extractor": {"foreach": "genres[*]", "path": "name"},
        },
    ]),
])
def test_scrape_should_produce_list_for_multivalued_rule(
    doctype: DocType,
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules})
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {"genres": ["Horror", "Drama"]}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {
            "key": "title",
            "extractor": {"path": "//title/text()"},
        },
        {
            "key": "foos",
            "extractor": {"foreach": "//ul[@class='foos']/li", "path": "./text()"},
        },
    ]),
    ("json", [
        {
            "key": "title",
            "extractor": {"path": "title"},
        },
        {
            "key": "foos",
            "extractor": {"foreach": "foos[*]", "path": "text"},
        },
    ]),
])
def test_scrape_should_exclude_empty_items_in_multivalued_rule_results(
    doctype: DocType,
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules})
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {"title": "The Shining"}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {
            "key": "genres",
            "extractor": {
                "foreach": "//ul[@class='genres']/li",
                "path": "./text()",
                "transforms": ["lower"],
            },
        },
    ]),
    ("json", [
        {
            "key": "genres",
            "extractor": {
                "foreach": "genres[*]",
                "path": "name",
                "transforms": ["lower"],
            },
        },
    ]),
])
def test_scrape_should_transform_each_value_in_multivalued_result(
    doctype: DocType,
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules}, transformers=TRANSFORMERS)
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {"genres": ["horror", "drama"]}


@pytest.mark.parametrize(("doctype", "root", "rules"), [
    ("html", "//div[@class='director']", [
        {"key": "director", "extractor": {"path": "./p/a/text()"}},
    ]),
    ("json", "director", [
        {"key": "director", "extractor": {"path": "name"}},
    ]),
])
def test_scrape_should_move_root_before_starting(
    doctype: DocType,
    root: str,
    rules: list[Rule],
) -> None:
    spec = load_spec({"root": root, "rules": rules})
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {"director": "Stanley Kubrick"}


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {
            "key": "director",
            "extractor": {
                "rules": [
                    {
                        "key": "name",
                        "extractor": {
                            "path": "//div[@class='director']//a/text()",
                        },
                    },
                    {
                        "key": "id",
                        "extractor": {
                            "path": "//div[@class='director']//a/@href",
                            "transforms": ["id_from_link"],
                        },
                    },
                ],
            },
        },
    ]),
    ("json", [
        {
            "key": "director",
            "extractor": {
                "rules": [
                    {
                        "key": "name",
                        "extractor": {"path": "director.name"},
                    },
                    {
                        "key": "id",
                        "extractor": {"path": "director.id"},
                    },
                ],
            },
        },
    ]),
])
def test_scrape_should_produce_subitems_for_subrules(
    doctype: DocType,
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules}, transformers=TRANSFORMERS)
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {
        "director": {"name": "Stanley Kubrick", "id": 1},
    }


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {
            "key": "director",
            "extractor": {
                "root": "//div[@class='director']//a",
                "rules": [
                    {
                        "key": "name",
                        "extractor": {"path": "./text()"},
                    },
                    {
                        "key": "id",
                        "extractor": {"path": "./@href", "transforms": ["id_from_link"]},
                    },
                ],
            },
        },
    ]),
    ("json", [
        {
            "key": "director",
            "extractor": {
                "root": "director",
                "rules": [
                    {"key": "name", "extractor": {"path": "name"}},
                    {"key": "id", "extractor": {"path": "id"}},
                ],
            },
        },
    ]),
])
def test_scrape_should_move_root_for_subitems(
    doctype: DocType,
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules}, transformers=TRANSFORMERS)
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {
        "director": {"name": "Stanley Kubrick", "id": 1},
    }


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {
            "key": "cast",
            "extractor": {
                "foreach": "//table[@class='cast']/tr",
                "rules": [
                    {"key": "name", "extractor": {"path": "./td[1]/a/text()"}},
                    {"key": "character", "extractor": {"path": "./td[2]/text()"}},
                ],
            },
        },
    ]),
    ("json", [
        {
            "key": "cast",
            "extractor": {
                "foreach": "cast[*]",
                "rules": [
                    {"key": "name", "extractor": {"path": "name"}},
                    {"key": "character", "extractor": {"path": "character"}},
                ],
            },
        },
    ]),
])
def test_scrape_should_produce_subitem_lists_for_multivalued_subrules(
    doctype: DocType,
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules})
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {
        "cast": [
            {"name": "Jack Nicholson", "character": "Jack Torrance"},
            {"name": "Shelley Duvall", "character": "Wendy Torrance"},
        ],
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
                    {"key": "character", "extractor": {"path": "./td[2]/text()"}},
                ],
            },
        },
    ]),
    ("json", [
        {
            "key": "cast",
            "extractor": {
                "root": "cast",
                "foreach": "[*]",
                "rules": [
                    {"key": "name", "extractor": {"path": "name"}},
                    {"key": "character", "extractor": {"path": "character"}},
                ],
            },
        },
    ]),
])
def test_scrape_root_should_come_before_foreach(
    doctype: DocType,
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules})
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {
        "cast": [
            {"name": "Jack Nicholson", "character": "Jack Torrance"},
            {"name": "Shelley Duvall", "character": "Wendy Torrance"},
        ],
    }


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {
            "key": "cast",
            "extractor": {
                "foreach": "//table[@class='cast']/tr",
                "rules": [
                    {"key": "name", "extractor": {"path": "./td[1]/a/text()"}},
                    {"key": "character", "extractor": {"path": "./td[2]/text()"}},
                ],
                "transforms": ["stars"],
            },
        },
    ]),
    ("json", [
        {
            "key": "cast",
            "extractor": {
                "foreach": "cast[*]",
                "rules": [
                    {"key": "name", "extractor": {"path": "name"}},
                    {"key": "character", "extractor": {"path": "character"}},
                ],
                "transforms": ["stars"],
            },
        },
    ]),
])
def test_scrape_should_transform_subitems(
    doctype: DocType,
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules}, transformers=TRANSFORMERS)
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {
        "cast": [
            "Jack Nicholson as Jack Torrance",
            "Shelley Duvall as Wendy Torrance",
        ],
    }


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {
            "foreach": "//div[@class='info']",
            "key": {"path": "./h3/text()"},
            "extractor": {"path": "./p/text()"},
        },
    ]),
    ("json", [
        {
            "foreach": "info[*]",
            "key": {"path": "name"},
            "extractor": {"path": "value"},
        },
    ]),
])
def test_scrape_should_generate_keys_from_document(
    doctype: DocType,
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules})
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {
        "Country": "United States",
        "Language": "English",
    }


@pytest.mark.parametrize(("doctype", "rules"), [
    ("html", [
        {
            "foreach": "//div[@class='info']",
            "key": {"path": "./h3/text()", "transforms": ["lower"]},
            "extractor": {"path": "./p/text()"},
        },
    ]),
    ("json", [
        {
            "foreach": "info[*]",
            "key": {"path": "name", "transforms": ["lower"]},
            "extractor": {"path": "value"},
        },
    ]),
])
def test_scrape_should_transform_generated_key(
    doctype: DocType,
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules}, transformers=TRANSFORMERS)
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {
        "country": "United States",
        "language": "English",
    }


@pytest.mark.parametrize(("doctype", "pre", "rules"), [
    ("html", ["shorten_title"], [
        {"key": "title", "extractor": {"path": "//title/text()"}},
    ]),
    ("json", ["shorten_title"], [
        {"key": "title", "extractor": {"path": "title"}},
    ]),
])
def test_scrape_should_apply_preprocess(
    doctype: DocType,
    pre: list[str],
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules, "pre": pre}, preprocessors=PREPROCESSORS)
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {"title": "The Shinin"}


@pytest.mark.parametrize(("doctype", "pre", "rules"), [
    ("html", ["shorten_title", "shorten_title"], [
        {"key": "title", "extractor": {"path": "//title/text()"}},
    ]),
    ("json", ["shorten_title", "shorten_title"], [
        {"key": "title", "extractor": {"path": 'title'}},
    ]),
])
def test_scrape_should_apply_multiple_preprocesses(
    doctype: DocType,
    pre: list[str],
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules, "pre": pre}, preprocessors=PREPROCESSORS)
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {"title": "The Shini"}


@pytest.mark.parametrize(("doctype", "post", "rules"), [
    ("html", ["shorten_items"], [
        {"key": "title", "extractor": {"path": "//title/text()"}},
    ]),
    ("json", ["shorten_items"], [
        {"key": "title", "extractor": {"path": "title"}},
    ]),
])
def test_scrape_should_apply_postprocess(
    doctype: DocType,
    post: list[str],
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules, "post": post}, postprocessors=POSTPROCESSORS)
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {"titl": "The Shinin"}


@pytest.mark.parametrize(("doctype", "post", "rules"), [
    ("html", ["shorten_items", "shorten_items"], [
        {"key": "title", "extractor": {"path": "//title/text()"}},
    ]),
    ("json", ["shorten_items", "shorten_items"], [
        {"key": "title", "extractor": {"path": "title"}},
    ]),
])
def test_scrape_should_apply_multiple_postprocesses(
    doctype: DocType,
    post: list[str],
    rules: list[Rule],
) -> None:
    spec = load_spec({"rules": rules, "post": post}, postprocessors=POSTPROCESSORS)
    assert spec.scrape(MOVIE[doctype], doctype=doctype) == {"tit": "The Shini"}
