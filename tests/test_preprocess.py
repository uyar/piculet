from piculet import make_xpather as XPath
from piculet import make_path as Path
from piculet import preprocessors, transformers


def test_remove_should_remove_selected_element(shining):
    preprocessors.remove(path="//tr[1]")(shining)
    data = XPath("//tr/td/a/text()")(shining)
    assert data == ["Shelley Duvall"]


def test_remove_selected_none_should_not_cause_error(shining):
    preprocessors.remove(path="//tr[50]")(shining)
    data = XPath("//tr/td/a/text()")(shining)
    assert data == ["Jack Nicholson", "Shelley Duvall"]


def test_set_attr_value_from_str_should_set_attribute_for_selected_elements(shining):
    preprocessors.set_attr(path="//ul[@class='genres']/li", name="foo", value="bar")(shining)
    data = XPath("//li[@foo='bar']/text()")(shining)
    assert data == ["Horror", "Drama"]


def test_set_attr_value_from_path_should_set_attribute_for_selected_elements(shining):
    value = Path("./text()")
    preprocessors.set_attr(path="//ul[@class='genres']/li", name="foo", value=value)(shining)
    data = XPath("//li[@foo]/@foo")(shining)
    assert data == ["Horror", "Drama"]


def test_set_attr_value_from_path_empty_value_should_be_ignored(shining):
    value = Path("./@bar")
    preprocessors.set_attr(path="//ul[@class='genres']/li", name="foo", value=value)(shining)
    data = XPath("//li[@foo]/@foo")(shining)
    assert data == []


def test_set_attr_name_from_path_should_set_attribute_for_selected_elements(shining):
    name = Path("./text()")
    preprocessors.set_attr(path="//ul[@class='genres']/li", name=name, value="bar")(shining)
    data = XPath("//li[@Horror]/@Horror")(shining)
    assert data == ["bar"]


def test_set_attr_name_from_path_empty_value_should_be_ignored(shining):
    name = Path("./@bar")
    preprocessors.set_attr(path="//ul[@class='genres']/li", name=name, value="bar")(shining)
    data = XPath("//li[@Horror]/@Horror")(shining)
    assert data == []


def test_set_attr_selected_none_should_not_cause_error(shining):
    preprocessors.set_attr(path="//foo", name="foo", value="bar")(shining)
    data = XPath("//li[@foo='bar']/@foo")(shining)
    assert data == []


def test_set_text_value_from_str_should_set_text_for_selected_elements(shining):
    preprocessors.set_text(path="//ul[@class='genres']/li", text="Foo")(shining)
    data = XPath("//ul[@class='genres']/li/text()")(shining)
    assert data == ["Foo", "Foo"]


def test_set_text_value_from_path_should_set_text_for_selected_elements(shining):
    text = Path("./text()", transform=transformers.lower)
    preprocessors.set_text(path="//ul[@class='genres']/li", text=text)(shining)
    data = XPath("//ul[@class='genres']/li/text()")(shining)
    assert data == ["horror", "drama"]


def test_set_text_empty_value_should_be_ignored(shining):
    text = Path("./@foo")
    preprocessors.set_text(path="//ul[@class='genres']/li", text=text)(shining)
    data = XPath("//ul[@class='genres']/li/text()")(shining)
    assert data == []
