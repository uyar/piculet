from pytest import mark

from piculet import HTMLNormalizer


normalize = HTMLNormalizer()


def test_normalize_well_formed_xml_should_succeed():
    content = """<html></html>"""
    assert normalize(content) == """<html></html>"""


def test_normalize_doctype_should_be_removed():
    content = """<!DOCTYPE html><html></html>"""
    assert normalize(content) == """<html></html>"""


def test_normalize_comment_should_be_removed():
    content = """<html><!-- comment --></html>"""
    assert normalize(content) == """<html></html>"""


def test_normalize_insignificant_whitespace_should_be_removed():
    content = """<html    lang = "en" ></html>"""
    assert normalize(content) == """<html lang="en"></html>"""


def test_normalize_self_closing_tags_should_have_slash_at_end():
    content = """<br>"""
    assert normalize(content) == """<br/>"""


def test_normalize_self_closing_tags_should_not_have_closing_tags():
    content = """<br/>"""
    assert normalize(content) == """<br/>"""


def test_normalize_attributes_should_have_values():
    content = """<option checked></option>"""
    assert normalize(content) == """<option checked=""></option>"""


def test_normalize_attribute_values_should_have_quotes():
    content = """<html lang=en></html>"""
    assert normalize(content) == """<html lang="en"></html>"""


def test_normalize_multiple_attributes_should_work():
    content = """<option value=op1 checked></option>"""
    assert normalize(content) == """<option value="op1" checked=""></option>"""


@mark.parametrize(("entity", "ref"), [
    ("&", "&amp;"),
    ("<", "&lt;"),
    (">", "&gt;"),
])
def test_normalize_entities_should_be_replaced_in_data(entity, ref):
    content = f"""<p>{entity}</p>"""
    assert normalize(content) == f"""<p>{ref}</p>"""


@mark.parametrize(("entity", "ref"), [
    ("&", "&amp;"),
    ("<", "&lt;"),
    (">", "&gt;"),
    ("&#x22;", "&quot;"),
])
def test_normalize_entities_should_be_replaced_in_attribute_values(entity, ref):
    content = f"""<p id="{entity}"></p>"""
    assert normalize(content) == f"""<p id="{ref}"></p>"""


def test_normalize_unicode_data_should_be_preserved():
    content = """<p>ğış</p>"""
    assert normalize(content) == """<p>ğış</p>"""


def test_normalize_unicode_attribute_value_should_be_preserved():
    content = """<p foo="ğış"></p>"""
    assert normalize(content) == """<p foo="ğış"></p>"""
