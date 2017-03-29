from pytest import fixture, mark, raises
from unittest.mock import patch

from hashlib import md5
from io import StringIO

import json
import os
import socket

import piculet


base_dir = os.path.dirname(__file__)
infile = os.path.join(base_dir, 'files', 'utf-8_charset_utf-8.html')
wikipedia_spec = os.path.join(base_dir, '..', 'examples', 'wikipedia.json')
wikipedia_bowie = 'https://en.wikipedia.org/wiki/David_Bowie'
wikipedia_bowie_hash = md5(wikipedia_bowie.encode('utf-8')).hexdigest()
wikipedia_bowie_cache = os.path.join(base_dir, '.cache', wikipedia_bowie_hash)


@fixture
def disable_internet(request):
    def guard(*args, **kwargs):
        raise RuntimeError('Internet access disabled')

    def finalize():
        socket.socket = old_socket

    old_socket = socket.socket
    socket.socket = guard
    request.addfinalizer(finalize)


@fixture(scope='module', autouse=True)
def cache_test_page():
    """Store the test page in the cache."""
    piculet.get_document(wikipedia_bowie)


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
    assert 'required: command' in err


def test_invalid_command_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'foo'])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert 'invalid choice: \'foo\'' in err


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
    assert 'following arguments are required: file' in err


def test_h2x_should_read_given_file(capsys):
    with open(infile) as f:
        content = f.read()
    piculet.main(argv=['piculet', 'h2x', infile])
    out, err = capsys.readouterr()
    assert out == content


def test_h2x_should_read_stdin_when_input_is_dash(capsys):
    with open(infile) as f:
        content = f.read()
    with patch('sys.stdin', StringIO(content)):
        piculet.main(argv=['piculet', 'h2x', '-'])
    out, err = capsys.readouterr()
    assert out == content


def test_scrape_no_url_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'scrape', '-s', wikipedia_spec, '-r', 'person'])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert 'following arguments are required: url' in err


def test_scrape_no_spec_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'scrape', wikipedia_bowie, '-r', 'person'])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert 'following arguments are required: -s' in err


def test_scrape_missing_spec_file_should_fail_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'scrape', wikipedia_bowie, '-s', 'foo.json',
                           '-r', 'person'])
    out, err = capsys.readouterr()
    assert 'No such file or directory: ' in err


def test_scrape_no_rules_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'scrape', wikipedia_bowie, '-s', wikipedia_spec])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert 'following arguments are required: -r' in err


def test_scrape_unknown_rules_should_print_error_message_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'scrape', wikipedia_bowie, '-s', wikipedia_spec,
                           '-r', 'foo'])
    out, err = capsys.readouterr()
    assert 'Rules not found: ' in err


def test_scrape_should_scrape_given_url(capsys):
    piculet.main(argv=['piculet', 'scrape', wikipedia_bowie, '-s', wikipedia_spec,
                       '-r', 'person', '--html'])
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert data['name'] == 'David Bowie'


def test_scrape_cached_should_read_from_disk(capsys, disable_internet):
    assert os.path.exists(wikipedia_bowie_cache)
    piculet.main(argv=['piculet', 'scrape', wikipedia_bowie, '-s', wikipedia_spec,
                       '-r', 'person', '--html'])
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert data['name'] == 'David Bowie'


@mark.download
def test_scrape_cache_disabled_should_retrieve_from_web(capsys):
    assert os.path.exists(wikipedia_bowie_cache)
    os.rename(wikipedia_bowie_cache, wikipedia_bowie_cache + '.BACKUP')
    cache_dir = os.environ['PICULET_WEB_CACHE']  # backup cache dir
    del os.environ['PICULET_WEB_CACHE']
    piculet.main(argv=['piculet', 'scrape', wikipedia_bowie, '-s', wikipedia_spec,
                       '-r', 'person', '--html'])
    os.environ['PICULET_WEB_CACHE'] = cache_dir  # restore cache dir
    assert not os.path.exists(wikipedia_bowie_cache)
    os.rename(wikipedia_bowie_cache + '.BACKUP', wikipedia_bowie_cache)
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert data['name'] == 'David Bowie'


@mark.download
def test_scrape_uncached_should_retrieve_from_web(capsys):
    assert os.path.exists(wikipedia_bowie_cache)
    os.rename(wikipedia_bowie_cache, wikipedia_bowie_cache + '.BACKUP')
    piculet.main(argv=['piculet', 'scrape', wikipedia_bowie, '-s', wikipedia_spec,
                       '-r', 'person', '--html'])
    assert os.path.exists(wikipedia_bowie_cache)
    os.rename(wikipedia_bowie_cache + '.BACKUP', wikipedia_bowie_cache)
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert data['name'] == 'David Bowie'
