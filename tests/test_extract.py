import pytest

from piculet import Path, Piculet, Rule, build_tree


def test_empty_rules_should_return_empty_result(examples):
    data = Piculet([]).extract(examples.shining)
    assert data == {}


def test_extracted_text_should_be_scalar(examples):
    rules = [Rule("title", Path("//title/text()"))]
    data = Piculet(rules).extract(examples.shining)
    assert data == {"title": "The Shining"}


def test_extracted_texts_should_be_concatenated(examples):
    rules = [Rule("full_title", Path("//h1//text()"))]
    data = Piculet(rules).extract(examples.shining)
    assert data == {"full_title": "The Shining (1980)"}


def test_extracted_texts_should_be_concatenated_using_given_separator(examples):
    rules = [Rule("cast_names", Path('//table[@class="cast"]/tr/td[1]/a/text()', sep=", "))]
    data = Piculet(rules).extract(examples.shining)
    assert data == {"cast_names": "Jack Nicholson, Shelley Duvall"}


def test_extracted_text_should_be_transformable(examples):
    rules = [Rule("year", Path('//span[@class="year"]/text()', transform=int))]
    data = Piculet(rules).extract(examples.shining)
    assert data == {"year": 1980}


def test_multiple_rules_should_generate_multiple_items(examples):
    rules = [
        Rule("title", Path("//title/text()")),
        Rule("year", Path('//span[@class="year"]/text()', transform=int)),
    ]
    data = Piculet(rules).extract(examples.shining)
    assert data == {"title": "The Shining", "year": 1980}


def test_item_with_no_data_should_be_excluded(examples):
    rules = [
        Rule("title", Path("//title/text()")),
        Rule("foo", Path("//foo/text()")),
    ]
    data = Piculet(rules).extract(examples.shining)
    assert data == {"title": "The Shining"}


def test_item_with_empty_str_value_should_be_included():
    content = '<root><foo val=""/></root>'
    rules = [Rule("foo", Path("//foo/@val"))]
    data = Piculet(rules).extract(build_tree(content))
    assert data == {"foo": ""}


def test_item_with_zero_value_should_be_included():
    content = '<root><foo val="0"/></root>'
    rules = [Rule("foo", Path("//foo/@val", transform=int))]
    data = Piculet(rules).extract(build_tree(content))
    assert data == {"foo": 0}


def test_item_with_false_value_should_be_included():
    content = '<root><foo val=""/></root>'
    rules = [Rule("foo", Path("//foo/@val", transform=bool))]
    data = Piculet(rules).extract(build_tree(content))
    assert data == {"foo": False}


def test_multivalued_item_should_be_list(examples):
    rules = [Rule("genres", Path(foreach='//ul[@class="genres"]/li', path="./text()"))]
    data = Piculet(rules).extract(examples.shining)
    assert data == {"genres": ["Horror", "Drama"]}


def test_multivalued_items_should_be_transformable(examples):
    rules = [Rule("genres", Path(foreach='//ul[@class="genres"]/li', path="./text()", transform=str.lower))]
    data = Piculet(rules).extract(examples.shining)
    assert data == {"genres": ["horror", "drama"]}


def test_empty_values_should_be_excluded_from_multivalued_item_list(examples):
    rules = [Rule("foos", Path(foreach='//ul[@class="foos"]/li', path="./text()"))]
    data = Piculet(rules).extract(examples.shining)
    assert data == {}


def test_subrules_should_generate_subitems(examples):
    rules = [
        Rule(
            "director",
            Piculet(
                [
                    Rule("name", Path('//div[@class="director"]//a/text()')),
                    Rule("link", Path('//div[@class="director"]//a/@href')),
                ]
            ),
        )
    ]
    data = Piculet(rules).extract(examples.shining)
    assert data == {"director": {"link": "/people/1", "name": "Stanley Kubrick"}}


def test_multivalued_subrules_should_generate_list_of_subitems(examples):
    rules = [
        Rule(
            "cast",
            Piculet(
                foreach='//table[@class="cast"]/tr',
                rules=[
                    Rule("name", Path("./td[1]/a/text()")),
                    Rule("character", Path("./td[2]/text()")),
                ],
            ),
        )
    ]
    data = Piculet(rules).extract(examples.shining)
    assert data == {
        "cast": [
            {"character": "Jack Torrance", "name": "Jack Nicholson"},
            {"character": "Wendy Torrance", "name": "Shelley Duvall"},
        ]
    }


def test_subitems_should_be_transformable(examples):
    rules = [
        Rule(
            "cast",
            Piculet(
                foreach='//table[@class="cast"]/tr',
                rules=[
                    Rule("name", Path("./td[1]/a/text()")),
                    Rule("character", Path("./td[2]/text()")),
                ],
                transform=lambda x: "%(name)s as %(character)s" % x,
            ),
        )
    ]
    data = Piculet(rules).extract(examples.shining)
    assert data == {"cast": ["Jack Nicholson as Jack Torrance", "Shelley Duvall as Wendy Torrance"]}


def test_key_should_be_generatable_using_path(examples):
    rules = [Rule(foreach='//div[@class="info"]', key=Path("./h3/text()"), value=Path("./p/text()"))]
    data = Piculet(rules).extract(examples.shining)
    assert data == {"Language:": "English", "Runtime:": "144 minutes"}


def test_generated_key_should_be_transformable(examples):
    rules = [
        Rule(
            foreach='//div[@class="info"]',
            key=Path("./h3/text()", transform=lambda s: s.lower()[:-1]),
            value=Path("./p/text()"),
        )
    ]
    data = Piculet(rules).extract(examples.shining)
    assert data == {"language": "English", "runtime": "144 minutes"}


def test_generated_key_none_should_be_excluded(examples):
    rules = [Rule(foreach='//div[@class="info"]', key=Path("./foo/text()"), value=Path("./p/text()"))]
    data = Piculet(rules).extract(examples.shining)
    assert data == {}


def test_section_should_set_root_for_queries(examples):
    rules = [
        Rule(
            "director",
            Piculet(
                section='//div[@class="director"]//a',
                rules=[
                    Rule("name", Path("./text()")),
                    Rule("link", Path("./@href")),
                ],
            ),
        )
    ]
    data = Piculet(rules).extract(examples.shining)
    assert data == {"director": {"link": "/people/1", "name": "Stanley Kubrick"}}


def test_section_no_roots_should_return_empty_result(examples):
    rules = [Rule("director", Piculet(section="//foo", rules=[Rule("name", Path("./text()"))]))]
    data = Piculet(rules).extract(examples.shining)
    assert data == {}


def test_section_multiple_roots_should_raise_error(examples):
    with pytest.raises(ValueError):
        rules = [Rule("director", Piculet(section="//div", rules=[Rule("name", Path("./text()"))]))]
        Piculet(rules).extract(examples.shining)
