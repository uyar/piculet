import pytest

from piculet import build_tree, reducers, transformers
from piculet import make_item_maker as Item
from piculet import make_items_extractor as Extractor
from piculet import make_path_extractor as Path


def test_no_rules_should_return_empty_result(shining):
    data = Extractor([])(shining)
    assert data == {}


def test_extracted_value_should_be_reduced(shining):
    items = [Item(key="title", value=Path("//title/text()", reduce=reducers.first))]
    data = Extractor(items)(shining)
    assert data == {"title": "The Shining"}


def test_default_reducer_should_be_concat(shining):
    items = [Item(key="full_title", value=Path("//h1//text()"))]
    data = Extractor(items)(shining)
    assert data == {"full_title": "The Shining (1980)"}


def test_added_reducer_should_be_usable(shining):
    reducers.second = lambda x: x[1]
    items = [Item(key="year", value=Path("//h1//text()", reduce=reducers.second))]
    data = Extractor(items)(shining)
    assert data == {"year": "1980"}


def test_reduce_by_lambda_should_be_ok(shining):
    items = [Item(key="title", value=Path("//title/text()", reduce=lambda xs: xs[0]))]
    data = Extractor(items)(shining)
    assert data == {"title": "The Shining"}


def test_reduced_value_should_be_transformable(shining):
    items = [Item(key="year", value=Path('//span[@class="year"]/text()', transform=int))]
    data = Extractor(items)(shining)
    assert data == {"year": 1980}


def test_added_transformer_should_be_usable(shining):
    transformers.year25 = lambda x: int(x) + 25
    items = [
        Item(
            key="year",
            value=Path('//span[@class="year"]/text()', transform=transformers.year25),
        )
    ]
    data = Extractor(items)(shining)
    assert data == {"year": 2005}


def test_multiple_rules_should_generate_multiple_items(shining):
    items = [
        Item(key="title", value=Path("//title/text()")),
        Item("year", value=Path('//span[@class="year"]/text()', transform=int)),
    ]
    data = Extractor(items)(shining)
    assert data == {"title": "The Shining", "year": 1980}


def test_item_with_no_data_should_be_excluded(shining):
    items = [
        Item(key="title", value=Path("//title/text()")),
        Item(key="foo", value=Path("//foo/text()")),
    ]
    data = Extractor(items)(shining)
    assert data == {"title": "The Shining"}


def test_item_with_empty_str_value_should_be_included():
    content = '<root><foo val=""/></root>'
    items = [Item(key="foo", value=Path("//foo/@val"))]
    data = Extractor(items)(build_tree(content))
    assert data == {"foo": ""}


def test_item_with_zero_value_should_be_included():
    content = '<root><foo val="0"/></root>'
    items = [Item(key="foo", value=Path("//foo/@val", transform=int))]
    data = Extractor(items)(build_tree(content))
    assert data == {"foo": 0}


def test_item_with_false_value_should_be_included():
    content = '<root><foo val=""/></root>'
    items = [Item(key="foo", value=Path("//foo/@val", transform=bool))]
    data = Extractor(items)(build_tree(content))
    assert data == {"foo": False}


def test_multivalued_item_should_be_list(shining):
    items = [
        Item(key="genres", value=Path(foreach='//ul[@class="genres"]/li', path="./text()"))
    ]
    data = Extractor(items)(shining)
    assert data == {"genres": ["Horror", "Drama"]}


def test_multivalued_items_should_be_transformable(shining):
    items = [
        Item(
            key="genres",
            value=Path(
                foreach='//ul[@class="genres"]/li',
                path="./text()",
                transform=transformers.lower,
            ),
        )
    ]
    data = Extractor(items)(shining)
    assert data == {"genres": ["horror", "drama"]}


def test_empty_values_should_be_excluded_from_multivalued_item_list(shining):
    items = [Item(key="foos", value=Path(foreach='//ul[@class="foos"]/li', path="./text()"))]
    data = Extractor(items)(shining)
    assert data == {}


def test_subrules_should_generate_subitems(shining):
    items = [
        Item(
            key="director",
            value=Extractor(
                items=[
                    Item(key="name", value=Path('//div[@class="director"]//a/text()')),
                    Item(key="link", value=Path('//div[@class="director"]//a/@href')),
                ]
            ),
        )
    ]
    data = Extractor(items)(shining)
    assert data == {"director": {"link": "/people/1", "name": "Stanley Kubrick"}}


def test_multivalued_subrules_should_generate_list_of_subitems(shining):
    items = [
        Item(
            key="cast",
            value=Extractor(
                foreach='//table[@class="cast"]/tr',
                items=[
                    Item(key="name", value=Path("./td[1]/a/text()")),
                    Item(key="character", value=Path("./td[2]/text()")),
                ],
            ),
        )
    ]
    data = Extractor(items)(shining)
    assert data == {
        "cast": [
            {"character": "Jack Torrance", "name": "Jack Nicholson"},
            {"character": "Wendy Torrance", "name": "Shelley Duvall"},
        ]
    }


def test_subitems_should_be_transformable(shining):
    items = [
        Item(
            key="cast",
            value=Extractor(
                foreach='//table[@class="cast"]/tr',
                items=[
                    Item(key="name", value=Path("./td[1]/a/text()")),
                    Item(key="character", value=Path("./td[2]/text()")),
                ],
                transform=lambda x: "%(name)s as %(character)s" % x,
            ),
        )
    ]
    data = Extractor(items)(shining)
    assert data == {
        "cast": ["Jack Nicholson as Jack Torrance", "Shelley Duvall as Wendy Torrance"]
    }


def test_key_should_be_generatable_using_path(shining):
    items = [
        Item(foreach='//div[@class="info"]', key=Path("./h3/text()"), value=Path("./p/text()"))
    ]
    data = Extractor(items)(shining)
    assert data == {"Language:": "English", "Runtime:": "144 minutes"}


def test_generated_key_should_be_normalizable(shining):
    items = [
        Item(
            foreach='//div[@class="info"]',
            key=Path("./h3/text()", reduce=reducers.normalize),
            value=Path("./p/text()"),
        )
    ]
    data = Extractor(items)(shining)
    assert data == {"language": "English", "runtime": "144 minutes"}


def test_generated_key_should_be_transformable(shining):
    items = [
        Item(
            foreach='//div[@class="info"]',
            key=Path("./h3/text()", reduce=reducers.normalize, transform=lambda x: x.upper()),
            value=Path("./p/text()"),
        )
    ]
    data = Extractor(items)(shining)
    assert data == {"LANGUAGE": "English", "RUNTIME": "144 minutes"}


def test_generated_key_none_should_be_excluded(shining):
    items = [
        Item(foreach='//div[@class="info"]', key=Path("./foo/text()"), value=Path("./p/text()"))
    ]
    data = Extractor(items)(shining)
    assert data == {}


def test_section_should_set_root_for_queries(shining):
    items = [
        Item(
            key="director",
            value=Extractor(
                section='//div[@class="director"]//a',
                items=[
                    Item(key="name", value=Path("./text()")),
                    Item(key="link", value=Path("./@href")),
                ],
            ),
        )
    ]
    data = Extractor(items)(shining)
    assert data == {"director": {"link": "/people/1", "name": "Stanley Kubrick"}}


def test_section_no_roots_should_return_empty_result(shining):
    items = [
        Item(
            key="director",
            value=Extractor(section="//foo", items=[Item(key="name", value=Path("./text()"))]),
        )
    ]
    data = Extractor(items)(shining)
    assert data == {}


def test_section_multiple_roots_should_raise_error(shining):
    with pytest.raises(ValueError):
        items = [
            Item(
                key="director",
                value=Extractor(
                    section="//div", items=[Item(key="name", value=Path("./text()"))]
                ),
            )
        ]
        Extractor(items)(shining)
