import pytest

from piculet import build_tree, pipe, transformers
from piculet import make_items as Items
from piculet import make_path as Path
from piculet import make_rule as Rule


def test_empty_rules_should_return_empty_result(shining):
    data = Items([])(shining)
    assert data == {}


def test_extracted_text_should_be_scalar(shining):
    rules = [Rule(key="title", value=Path("//title/text()"))]
    data = Items(rules)(shining)
    assert data == {"title": "The Shining"}


def test_extracted_texts_should_be_concatenated(shining):
    rules = [Rule(key="full_title", value=Path("//h1//text()"))]
    data = Items(rules)(shining)
    assert data == {"full_title": "The Shining (1980)"}


def test_extracted_text_should_be_transformable(shining):
    rules = [Rule(key="year", value=Path('//span[@class="year"]/text()', transform=int))]
    data = Items(rules)(shining)
    assert data == {"year": 1980}


def test_transformers_should_be_chainable(shining):
    rules = [
        Rule(
            key="century",
            value=Path(
                '//span[@class="year"]/text()', transform=pipe(int, lambda x: x // 100 + 1)
            ),
        )
    ]
    data = Items(rules)(shining)
    assert data == {"century": 20}


def test_added_transformer_should_be_usable(shining):
    transformers.year25 = lambda x: int(x) + 25
    rules = [
        Rule(
            key="year",
            value=Path('//span[@class="year"]/text()', transform=transformers.year25),
        )
    ]
    data = Items(rules)(shining)
    assert data == {"year": 2005}


def test_multiple_rules_should_generate_multiple_items(shining):
    rules = [
        Rule(key="title", value=Path("//title/text()")),
        Rule("year", value=Path('//span[@class="year"]/text()', transform=int)),
    ]
    data = Items(rules)(shining)
    assert data == {"title": "The Shining", "year": 1980}


def test_item_with_no_data_should_be_excluded(shining):
    rules = [
        Rule(key="title", value=Path("//title/text()")),
        Rule(key="foo", value=Path("//foo/text()")),
    ]
    data = Items(rules)(shining)
    assert data == {"title": "The Shining"}


def test_item_with_empty_str_value_should_be_included():
    content = '<root><foo val=""/></root>'
    rules = [Rule(key="foo", value=Path("//foo/@val"))]
    data = Items(rules)(build_tree(content))
    assert data == {"foo": ""}


def test_item_with_zero_value_should_be_included():
    content = '<root><foo val="0"/></root>'
    rules = [Rule(key="foo", value=Path("//foo/@val", transform=int))]
    data = Items(rules)(build_tree(content))
    assert data == {"foo": 0}


def test_item_with_false_value_should_be_included():
    content = '<root><foo val=""/></root>'
    rules = [Rule(key="foo", value=Path("//foo/@val", transform=bool))]
    data = Items(rules)(build_tree(content))
    assert data == {"foo": False}


def test_multivalued_item_should_be_list(shining):
    rules = [
        Rule(key="genres", value=Path(foreach='//ul[@class="genres"]/li', path="./text()"))
    ]
    data = Items(rules)(shining)
    assert data == {"genres": ["Horror", "Drama"]}


def test_multivalued_items_should_be_transformable(shining):
    rules = [
        Rule(
            key="genres",
            value=Path(
                foreach='//ul[@class="genres"]/li',
                path="./text()",
                transform=transformers.lower,
            ),
        )
    ]
    data = Items(rules)(shining)
    assert data == {"genres": ["horror", "drama"]}


def test_empty_values_should_be_excluded_from_multivalued_item_list(shining):
    rules = [Rule(key="foos", value=Path(foreach='//ul[@class="foos"]/li', path="./text()"))]
    data = Items(rules)(shining)
    assert data == {}


def test_subrules_should_generate_subitems(shining):
    rules = [
        Rule(
            key="director",
            value=Items(
                rules=[
                    Rule(key="name", value=Path('//div[@class="director"]//a/text()')),
                    Rule(key="link", value=Path('//div[@class="director"]//a/@href')),
                ]
            ),
        )
    ]
    data = Items(rules)(shining)
    assert data == {"director": {"link": "/people/1", "name": "Stanley Kubrick"}}


def test_multivalued_subrules_should_generate_list_of_subitems(shining):
    rules = [
        Rule(
            key="cast",
            value=Items(
                foreach='//table[@class="cast"]/tr',
                rules=[
                    Rule(key="name", value=Path("./td[1]/a/text()")),
                    Rule(key="character", value=Path("./td[2]/text()")),
                ],
            ),
        )
    ]
    data = Items(rules)(shining)
    assert data == {
        "cast": [
            {"character": "Jack Torrance", "name": "Jack Nicholson"},
            {"character": "Wendy Torrance", "name": "Shelley Duvall"},
        ]
    }


def test_subitems_should_be_transformable(shining):
    rules = [
        Rule(
            key="cast",
            value=Items(
                foreach='//table[@class="cast"]/tr',
                rules=[
                    Rule(key="name", value=Path("./td[1]/a/text()")),
                    Rule(key="character", value=Path("./td[2]/text()")),
                ],
                transform=lambda x: "%(name)s as %(character)s" % x,
            ),
        )
    ]
    data = Items(rules)(shining)
    assert data == {
        "cast": ["Jack Nicholson as Jack Torrance", "Shelley Duvall as Wendy Torrance"]
    }


def test_key_should_be_generatable_using_path(shining):
    rules = [
        Rule(foreach='//div[@class="info"]', key=Path("./h3/text()"), value=Path("./p/text()"))
    ]
    data = Items(rules)(shining)
    assert data == {"Language:": "English", "Runtime:": "144 minutes"}


def test_generated_key_should_be_transformable(shining):
    rules = [
        Rule(
            foreach='//div[@class="info"]',
            key=Path("./h3/text()", transform=transformers.normalize),
            value=Path("./p/text()"),
        )
    ]
    data = Items(rules)(shining)
    assert data == {"language": "English", "runtime": "144 minutes"}


def test_generated_key_none_should_be_excluded(shining):
    rules = [
        Rule(foreach='//div[@class="info"]', key=Path("./foo/text()"), value=Path("./p/text()"))
    ]
    data = Items(rules)(shining)
    assert data == {}


def test_section_should_set_root_for_queries(shining):
    rules = [
        Rule(
            key="director",
            value=Items(
                section='//div[@class="director"]//a',
                rules=[
                    Rule(key="name", value=Path("./text()")),
                    Rule(key="link", value=Path("./@href")),
                ],
            ),
        )
    ]
    data = Items(rules)(shining)
    assert data == {"director": {"link": "/people/1", "name": "Stanley Kubrick"}}


def test_section_no_roots_should_return_empty_result(shining):
    rules = [
        Rule(
            key="director",
            value=Items(section="//foo", rules=[Rule(key="name", value=Path("./text()"))]),
        )
    ]
    data = Items(rules)(shining)
    assert data == {}


def test_section_multiple_roots_should_raise_error(shining):
    with pytest.raises(ValueError):
        rules = [
            Rule(
                key="director",
                value=Items(section="//div", rules=[Rule(key="name", value=Path("./text()"))]),
            )
        ]
        Items(rules)(shining)
