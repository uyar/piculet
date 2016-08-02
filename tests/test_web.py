from pytest import fixture, raises

from subprocess import Popen
from time import sleep
from urllib.error import HTTPError

import os

from woody import retrieve, html_to_xhtml


@fixture(scope='module')
def web_server(request):
    """Address of local web server for serving test files."""
    port = 2016

    command = ['python3', '-m', 'http.server', str(port), '--bind', '127.0.0.1']
    process = Popen(command, cwd=os.path.dirname(__file__))
    sleep(0.5)

    def finalize():
        process.kill()

    request.addfinalizer(finalize)
    return 'http://127.0.0.1:{}/files'.format(port)


def test_retrieve_url_not_found_should_raise_http_error(web_server):
    url = '{}/utf-8_charset_utf-9.html'.format(web_server)
    with raises(HTTPError):
        retrieve(url)


def test_retrieve_meta_charset_correct_should_succeed(web_server):
    url = '{}/utf-8_charset_utf-8.html'.format(web_server)
    content = retrieve(url)
    assert 'ğışĞİŞ' in content


def test_retrieve_meta_content_type_correct_should_succeed(web_server):
    url = '{}/utf-8_content-type_utf-8.html'.format(web_server)
    content = retrieve(url)
    assert 'ğışĞİŞ' in content


def test_retrieve_meta_charset_incorrect_should_fail(web_server):
    url = '{}/utf-8_charset_iso8859-9.html'.format(web_server)
    content = retrieve(url)
    assert 'ğışĞİŞ' not in content


def test_retrieve_meta_content_type_incorrect_should_fail(web_server):
    url = '{}/utf-8_content-type_iso8859-9.html'.format(web_server)
    content = retrieve(url)
    assert 'ğışĞİŞ' not in content


def test_retrieve_meta_charset_incompatible_should_raise_unicode_error(web_server):
    url = '{}/iso8859-9_charset_utf-8.html'.format(web_server)
    with raises(UnicodeDecodeError):
        retrieve(url)


def test_retrieve_meta_content_type_incompatible_should_raise_unicode_error(web_server):
    url = '{}/iso8859-9_content-type_utf-8.html'.format(web_server)
    with raises(UnicodeDecodeError):
        retrieve(url)


def test_retrieve_requested_charset_correct_should_succeed(web_server):
    url = '{}/utf-8_charset_iso8859-9.html'.format(web_server)
    content = retrieve(url, charset='utf-8')
    assert 'ğışĞİŞ' in content


def test_retrieve_requested_charset_incorrect_should_fail(web_server):
    url = '{}/utf-8_charset_utf-8.html'.format(web_server)
    content = retrieve(url, charset='iso8859-9')
    assert 'ğışĞİŞ' not in content


def test_retrieve_requested_charset_incompatible_should_raise_unicode_error(web_server):
    url = '{}/iso8859-9_charset_iso8859-9.html'.format(web_server)
    with raises(UnicodeDecodeError):
        retrieve(url, charset='utf-8')


def test_retrieve_fallback_default_correct_should_succeed(web_server):
    url = '{}/utf-8_charset_none.html'.format(web_server)
    content = retrieve(url)
    assert 'ğışĞİŞ' in content


def test_retrieve_fallback_correct_should_succeed(web_server):
    url = '{}/iso8859-9_charset_none.html'.format(web_server)
    content = retrieve(url, fallback_charset='iso8859-9')
    assert 'ğışĞİŞ' in content


def test_retrieve_fallback_incorrect_should_fail(web_server):
    url = '{}/iso8859-9_charset_none.html'.format(web_server)
    content = retrieve(url, fallback_charset='iso8859-1')
    assert 'ğışĞİŞ' not in content


def test_retrieve_fallback_incompatible_should_raise_unicode_error(web_server):
    url = '{}/iso8859-9_charset_none.html'.format(web_server)
    with raises(UnicodeDecodeError):
        retrieve(url, fallback_charset='utf-8')


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
