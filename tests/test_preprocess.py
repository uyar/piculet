from piculet import Path, preprocessors, transformers, xpath


def test_remove_should_remove_selected_element(examples):
    preprocessors.remove(path="//tr[1]")(examples.shining)
    data = xpath("//tr/td/a/text()")(examples.shining)
    assert data == ["Shelley Duvall"]


def test_remove_selected_none_should_not_cause_error(examples):
    preprocessors.remove(path="//tr[50]")(examples.shining)
    data = xpath("//tr/td/a/text()")(examples.shining)
    assert data == ["Jack Nicholson", "Shelley Duvall"]


def test_set_attr_value_from_str_should_set_attribute_for_selected_elements(examples):
    preprocessors.set_attr(path="//ul[@class='genres']/li", name="foo", value="bar")(examples.shining)
    data = xpath("//li[@foo='bar']/text()")(examples.shining)
    assert data == ["Horror", "Drama"]


def test_set_attr_value_from_path_should_set_attribute_for_selected_elements(examples):
    value = Path("./text()")
    preprocessors.set_attr(path="//ul[@class='genres']/li", name="foo", value=value)(examples.shining)
    data = xpath("//li[@foo]/@foo")(examples.shining)
    assert data == ["Horror", "Drama"]


def test_set_attr_value_from_path_empty_value_should_be_ignored(examples):
    value = Path("./@bar")
    preprocessors.set_attr(path="//ul[@class='genres']/li", name="foo", value=value)(examples.shining)
    data = xpath("//li[@foo]/@foo")(examples.shining)
    assert data == []


def test_set_attr_name_from_path_should_set_attribute_for_selected_elements(examples):
    name = Path("./text()")
    preprocessors.set_attr(path="//ul[@class='genres']/li", name=name, value="bar")(examples.shining)
    data = xpath("//li[@Horror]/@Horror")(examples.shining)
    assert data == ["bar"]


def test_set_attr_name_from_path_empty_value_should_be_ignored(examples):
    name = Path("./@bar")
    preprocessors.set_attr(path="//ul[@class='genres']/li", name=name, value="bar")(examples.shining)
    data = xpath("//li[@Horror]/@Horror")(examples.shining)
    assert data == []


def test_set_attr_selected_none_should_not_cause_error(examples):
    preprocessors.set_attr(path="//foo", name="foo", value="bar")(examples.shining)
    data = xpath("//li[@foo='bar']/@foo")(examples.shining)
    assert data == []


def test_set_text_value_from_str_should_set_text_for_selected_elements(examples):
    preprocessors.set_text(path="//ul[@class='genres']/li", text="Foo")(examples.shining)
    data = xpath("//ul[@class='genres']/li/text()")(examples.shining)
    assert data == ["Foo", "Foo"]


def test_set_text_value_from_path_should_set_text_for_selected_elements(examples):
    text = Path("./text()", transform=transformers.lower)
    preprocessors.set_text(path="//ul[@class='genres']/li", text=text)(examples.shining)
    data = xpath("//ul[@class='genres']/li/text()")(examples.shining)
    assert data == ["horror", "drama"]


def test_set_text_empty_value_should_be_ignored(examples):
    text = Path("./@foo")
    preprocessors.set_text(path="//ul[@class='genres']/li", text=text)(examples.shining)
    data = xpath("//ul[@class='genres']/li/text()")(examples.shining)
    assert data == []
