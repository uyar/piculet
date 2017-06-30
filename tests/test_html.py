# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from pytest import raises

import os

from piculet import decode_html, html_to_xhtml


def read_document(filename):
    path = os.path.join(os.path.dirname(__file__), 'files', filename)
    with open(path, 'rb') as f:
        content = f.read()
    return content


def test_decode_content_meta_charset_correct_should_succeed():
    content = read_document('utf-8_charset_utf-8.html')
    assert 'ğışĞİŞ' in decode_html(content)


def test_decode_content_meta_content_type_correct_should_succeed():
    content = read_document('utf-8_content-type_utf-8.html')
    assert 'ğışĞİŞ' in decode_html(content)


def test_decode_content_meta_charset_incorrect_should_fail():
    content = read_document('utf-8_charset_iso8859-9.html')
    assert 'ğışĞİŞ' not in decode_html(content)


def test_decode_content_meta_content_type_incorrect_should_fail():
    content = read_document('utf-8_content-type_iso8859-9.html')
    assert 'ğışĞİŞ' not in decode_html(content)


def test_decode_content_meta_charset_incompatible_should_raise_unicode_error():
    content = read_document('iso8859-9_charset_utf-8.html')
    with raises(UnicodeDecodeError):
        decode_html(content)


def test_decode_content_meta_content_type_incompatible_should_raise_unicode_error():
    content = read_document('iso8859-9_content-type_utf-8.html')
    with raises(UnicodeDecodeError):
        decode_html(content)


def test_decode_content_requested_charset_correct_should_succeed():
    content = read_document('utf-8_charset_iso8859-9.html')
    assert 'ğışĞİŞ' in decode_html(content, charset='utf-8')


def test_decode_content_requested_charset_incorrect_should_fail():
    content = read_document('utf-8_charset_utf-8.html')
    assert 'ğışĞİŞ' not in decode_html(content, charset='iso8859-9')


def test_decode_content_requested_charset_incompatible_should_raise_unicode_error():
    content = read_document('iso8859-9_charset_iso8859-9.html')
    with raises(UnicodeDecodeError):
        decode_html(content, charset='utf-8')


def test_decode_content_fallback_default_correct_should_succeed():
    content = read_document('utf-8_charset_none.html')
    assert 'ğışĞİŞ' in decode_html(content)


def test_decode_content_fallback_correct_should_succeed():
    content = read_document('iso8859-9_charset_none.html')
    assert 'ğışĞİŞ' in decode_html(content, fallback_charset='iso8859-9')


def test_decode_content_fallback_incorrect_should_fail():
    content = read_document('iso8859-9_charset_none.html')
    assert 'ğışĞİŞ' not in decode_html(content, fallback_charset='iso8859-1')


def test_decode_content_fallback_incompatible_should_raise_unicode_error():
    content = read_document('iso8859-9_charset_none.html')
    with raises(UnicodeDecodeError):
        decode_html(content, fallback_charset='utf-8')


def test_html_to_xhtml_well_formed_xml_should_succeed():
    content = '''<html></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html></html>'''


def test_html_to_xhtml_doctype_should_be_removed():
    content = '''<!DOCTYPE html><html></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html></html>'''


def test_html_to_xhtml_comment_should_be_removed():
    content = '''<html><!-- comment --></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html></html>'''


def test_html_to_xhtml_omitted_tags_should_be_removed():
    content = '''<html><p></p><font></font></html>'''
    normalized = html_to_xhtml(content, omit_tags={'font'})
    assert normalized == '''<html><p></p></html>'''


def test_html_to_xhtml_omitted_attributes_should_be_removed():
    content = '''<html><p font="times"></p></html>'''
    normalized = html_to_xhtml(content, omit_attrs={'font'})
    assert normalized == '''<html><p></p></html>'''


def test_html_to_xhtml_self_closing_tags_should_have_slash_at_end():
    content = '''<html><br></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html><br /></html>'''


def test_html_to_xhtml_attributes_should_have_values():
    content = '''<html><option checked></option></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html><option checked=""></option></html>'''


def test_html_to_xhtml_unclosed_tags_should_be_closed():
    content = '''<html><p></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html><p></p></html>'''


def test_html_to_xhtml_unclosed_lis_should_be_closed():
    content = '''<html><ul><li><li></li></ul></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html><ul><li></li><li></li></ul></html>'''


def test_html_to_xhtml_unclosed_last_lis_should_be_closed():
    content = '''<html><ul><li></li><li></ul></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html><ul><li></li><li></li></ul></html>'''


def test_html_to_xhtml_end_tag_without_start_tag_should_be_discarded():
    content = '''<html><p></p></p></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html><p></p></html>'''


def test_html_to_xhtml_incorrect_nesting_should_be_reordered():
    content = '''<html><div><p></div></p></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html><div><p></p></div></html>'''


def test_html_to_xhtml_ampersands_should_be_replaced_in_data():
    content = '''<html><p>&</p></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html><p>&amp;</p></html>'''


def test_html_to_xhtml_lts_should_be_replaced_in_data():
    content = '''<html><p><</p></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html><p>&lt;</p></html>'''


def test_html_to_xhtml_gts_should_be_replaced_in_data():
    content = '''<html><p>></p></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html><p>&gt;</p></html>'''


def test_html_to_xhtml_ampersands_should_be_replaced_in_attribute_values():
    content = '''<html><p id="&"></p></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html><p id="&amp;"></p></html>'''


def test_html_to_xhtml_lts_should_be_replaced_in_attribute_values():
    content = '''<html><p id="<"></p></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html><p id="&lt;"></p></html>'''


def test_html_to_xhtml_gts_should_be_replaced_in_attribute_values():
    content = '''<html><p id=">"></p></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html><p id="&gt;"></p></html>'''


def test_html_to_xhtml_quotes_should_be_replaced_in_attribute_values():
    content = '''<html><p id="&#x22;"></p></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html><p id="&quot;"></p></html>'''


def test_html_to_xhtml_unicode_data_should_be_preserved():
    content = '''<html><p>ğış</p></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html><p>ğış</p></html>'''


def test_html_to_xhtml_unicode_attribute_value_should_be_preserved():
    content = '''<html><p foo="ğış"></p></html>'''
    normalized = html_to_xhtml(content)
    assert normalized == '''<html><p foo="ğış"></p></html>'''
