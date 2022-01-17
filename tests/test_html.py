from piculet import html_to_xhtml


TEMPLATE = """<DOCTYPE html>
<html>
  <head>
    %(meta)s
  </head>
  <body>
    <p>ğışĞİŞ</p>
  </body>
</html>
"""


def read_document(actual, reported, tag):
    if reported == "none":
        meta = ""
    else:
        tag = (
            '<meta charset="%(charset)s" />'
            if tag == "charset"
            else '<meta http-equiv="content-type" content="text/html; charset=%(charset)s" />'
        )
        meta = tag % {"charset": reported}
    content = TEMPLATE % {"meta": meta}
    return content.encode(actual)


def test_html_to_xhtml_well_formed_xml_should_succeed():
    content = """<html></html>"""
    normalized = html_to_xhtml(content)
    assert normalized == """<html></html>"""


def test_html_to_xhtml_doctype_should_be_removed():
    content = """<!DOCTYPE html><html></html>"""
    normalized = html_to_xhtml(content)
    assert normalized == """<html></html>"""


def test_html_to_xhtml_comment_should_be_removed():
    content = """<html><!-- comment --></html>"""
    normalized = html_to_xhtml(content)
    assert normalized == """<html></html>"""


def test_html_to_xhtml_self_closing_tags_should_have_slash_at_end():
    content = """<html><br></html>"""
    normalized = html_to_xhtml(content)
    assert normalized == """<html><br/></html>"""


def test_html_to_xhtml_attributes_should_have_values():
    content = """<html><option checked></option></html>"""
    normalized = html_to_xhtml(content)
    assert normalized == """<html><option checked=""></option></html>"""


def test_html_to_xhtml_ampersands_should_be_replaced_in_data():
    content = """<html><p>&</p></html>"""
    normalized = html_to_xhtml(content)
    assert normalized == """<html><p>&amp;</p></html>"""


def test_html_to_xhtml_lts_should_be_replaced_in_data():
    content = """<html><p><</p></html>"""
    normalized = html_to_xhtml(content)
    assert normalized == """<html><p>&lt;</p></html>"""


def test_html_to_xhtml_gts_should_be_replaced_in_data():
    content = """<html><p>></p></html>"""
    normalized = html_to_xhtml(content)
    assert normalized == """<html><p>&gt;</p></html>"""


def test_html_to_xhtml_ampersands_should_be_replaced_in_attribute_values():
    content = """<html><p id="&"></p></html>"""
    normalized = html_to_xhtml(content)
    assert normalized == """<html><p id="&amp;"></p></html>"""


def test_html_to_xhtml_lts_should_be_replaced_in_attribute_values():
    content = """<html><p id="<"></p></html>"""
    normalized = html_to_xhtml(content)
    assert normalized == """<html><p id="&lt;"></p></html>"""


def test_html_to_xhtml_gts_should_be_replaced_in_attribute_values():
    content = """<html><p id=">"></p></html>"""
    normalized = html_to_xhtml(content)
    assert normalized == """<html><p id="&gt;"></p></html>"""


def test_html_to_xhtml_quotes_should_be_replaced_in_attribute_values():
    content = """<html><p id="&#x22;"></p></html>"""
    normalized = html_to_xhtml(content)
    assert normalized == """<html><p id="&quot;"></p></html>"""


def test_html_to_xhtml_unicode_data_should_be_preserved():
    content = """<html><p>ğış</p></html>"""
    normalized = html_to_xhtml(content)
    assert normalized == """<html><p>ğış</p></html>"""


def test_html_to_xhtml_unicode_attribute_value_should_be_preserved():
    content = """<html><p foo="ğış"></p></html>"""
    normalized = html_to_xhtml(content)
    assert normalized == """<html><p foo="ğış"></p></html>"""
