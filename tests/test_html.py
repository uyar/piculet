from pytest import mark

from piculet import html_to_xml


def test_html_to_xml_well_formed_xml_should_succeed():
    content = """<html></html>"""
    assert html_to_xml(content) == """<html></html>"""


def test_html_to_xml_doctype_should_be_removed():
    content = """<!DOCTYPE html><html></html>"""
    assert html_to_xml(content) == """<html></html>"""


def test_html_to_xml_comment_should_be_removed():
    content = """<html><!-- comment --></html>"""
    assert html_to_xml(content) == """<html></html>"""


def test_html_to_xml_insignificant_whitespace_should_be_removed():
    content = """<html    lang = "en" ></html>"""
    assert html_to_xml(content) == """<html lang="en"></html>"""


def test_html_to_xml_self_closing_tags_should_have_slash_at_end():
    content = """<br>"""
    assert html_to_xml(content) == """<br/>"""


def test_html_to_xml_self_closing_tags_should_not_have_closing_tags():
    content = """<br/>"""
    assert html_to_xml(content) == """<br/>"""


def test_html_to_xml_attributes_should_have_values():
    content = """<option checked></option>"""
    assert html_to_xml(content) == """<option checked=""></option>"""


def test_html_to_xml_attribute_values_should_have_quotes():
    content = """<html lang=en></html>"""
    assert html_to_xml(content) == """<html lang="en"></html>"""


def test_html_to_xml_multiple_attributes_should_work():
    content = """<option value=op1 checked></option>"""
    assert html_to_xml(content) == """<option value="op1" checked=""></option>"""


@mark.parametrize(("entity", "ref"), [
    ("&", "&amp;"),
    ("<", "&lt;"),
    (">", "&gt;"),
])
def test_html_to_xml_entities_should_be_replaced_in_data(entity, ref):
    content = f"""<p>{entity}</p>"""
    assert html_to_xml(content) == f"""<p>{ref}</p>"""


@mark.parametrize(("entity", "ref"), [
    ("&", "&amp;"),
    ("<", "&lt;"),
    (">", "&gt;"),
    ("&#x22;", "&quot;"),
])
def test_html_to_xml_entities_should_be_replaced_in_attribute_values(entity, ref):
    content = f"""<p id="{entity}"></p>"""
    assert html_to_xml(content) == f"""<p id="{ref}"></p>"""


def test_html_to_xml_unicode_data_should_be_preserved():
    content = """<p>ğış</p>"""
    assert html_to_xml(content) == """<p>ğış</p>"""


def test_html_to_xml_unicode_attribute_value_should_be_preserved():
    content = """<p foo="ğış"></p>"""
    assert html_to_xml(content) == """<p foo="ğış"></p>"""
