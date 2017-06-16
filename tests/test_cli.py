from __future__ import absolute_import, division, print_function, unicode_literals

from pytest import mark, raises

from io import StringIO

import json
import os

import piculet

if not piculet.PY3:
    from mock import patch
else:
    from unittest.mock import patch


base_dir = os.path.dirname(__file__)
infile = os.path.join(base_dir, 'files', 'utf-8_charset_utf-8.html')
wikipedia_spec = os.path.join(base_dir, '..', 'examples', 'wikipedia.json')


def test_help_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', '--help'])
    out, err = capsys.readouterr()
    assert out.startswith('usage: ')


def test_no_command_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet'])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert ('required: command' in err) or ('too few arguments' in err)


def test_invalid_command_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'foo'])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert ('invalid choice: \'foo\'' in err) or ('invalid choice: u\'foo\'' in err)


def test_unrecognized_arguments_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', '--foo', 'h2x', ''])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert 'unrecognized arguments: --foo' in err


def test_debug_mode_should_print_debug_messages_on_stderr(capsys):
    piculet.main(argv=['piculet', '--debug', 'h2x', infile])
    out, err = capsys.readouterr()
    assert 'running in debug mode' in err


def test_h2x_no_input_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'h2x'])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert ('required: file' in err) or ('too few arguments' in err)


def test_h2x_should_read_given_file(capsys):
    with open(infile, 'rb') as f:
        content = piculet.decode_html(f.read())
    piculet.main(argv=['piculet', 'h2x', infile])
    out, err = capsys.readouterr()
    assert out == content


def test_h2x_should_read_stdin_when_input_is_dash(capsys):
    with open(infile, 'rb') as f:
        content = piculet.decode_html(f.read())
    with patch('sys.stdin', StringIO(content)):
        piculet.main(argv=['piculet', 'h2x', '-'])
    out, err = capsys.readouterr()
    assert out == content


def test_scrape_no_url_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'scrape', '-s', wikipedia_spec])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert ('required: document' in err) or ('too few arguments' in err)


def test_scrape_no_spec_should_print_usage_and_exit(capsys, test_pages):
    url, _ = test_pages['bowie']
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'scrape', url])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert ('required: -s' in err) or ('--spec is required' in err)


def test_scrape_missing_spec_file_should_fail_and_exit(capsys, test_pages):
    url, _ = test_pages['bowie']
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'scrape', url, '-s', 'foo.json'])
    out, err = capsys.readouterr()
    assert 'No such file or directory: ' in err


def test_scrape_local_should_scrape_given_file(capsys):
    dirname = os.path.join(os.path.dirname(__file__), '..', 'examples')
    shining = os.path.join(dirname, 'shining.html')
    spec = os.path.join(dirname, 'movie.json')
    piculet.main(argv=['piculet', 'scrape', shining, '-s', spec])
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert data['title'] == 'The Shining'


def test_scrape_should_scrape_given_url(capsys, test_pages):
    url, _ = test_pages['bowie']
    piculet.main(argv=['piculet', 'scrape', url, '-s', wikipedia_spec, '--html'])
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert data['name'] == 'David Bowie'


def test_scrape_cached_should_read_from_disk(capsys, test_pages):
    url, cache = test_pages['bowie']
    assert os.path.exists(cache)
    piculet.main(argv=['piculet', 'scrape', url, '-s', wikipedia_spec, '--html'])
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert data['name'] == 'David Bowie'


@mark.download
def test_scrape_cache_disabled_should_retrieve_from_web(capsys, test_pages, enable_internet):
    cache_dir = os.environ['PICULET_WEB_CACHE']  # backup cache dir
    del os.environ['PICULET_WEB_CACHE']
    url, cache = test_pages['bowie']
    assert os.path.exists(cache)
    os.rename(cache, cache + '.BACKUP')
    try:
        piculet.main(argv=['piculet', 'scrape', url, '-s', wikipedia_spec, '--html'])
        assert not os.path.exists(cache)
        out, err = capsys.readouterr()
        data = json.loads(out)
        assert data['name'] == 'David Bowie'
    finally:
        os.rename(cache + '.BACKUP', cache)
        os.environ['PICULET_WEB_CACHE'] = cache_dir  # restore cache dir


@mark.download
def test_scrape_uncached_should_retrieve_from_web(capsys, test_pages, enable_internet):
    url, cache = test_pages['bowie']
    assert os.path.exists(cache)
    os.rename(cache, cache + '.BACKUP')
    try:
        piculet.main(argv=['piculet', 'scrape', url, '-s', wikipedia_spec, '--html'])
        assert os.path.exists(cache)
        out, err = capsys.readouterr()
        data = json.loads(out)
        assert data['name'] == 'David Bowie'
    finally:
        os.rename(cache + '.BACKUP', cache)
