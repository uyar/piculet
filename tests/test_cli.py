from pytest import mark, raises
from pytest import config as test_config
from unittest.mock import patch

from io import StringIO

import json
import os

import piculet


infile = os.path.join(os.path.dirname(__file__), 'files', 'utf-8_charset_utf-8.html')
wikipedia_spec = os.path.join(os.path.dirname(__file__), '..', 'examples', 'wikipedia.json')
wikipedia_bowie = 'https://en.wikipedia.org/wiki/David_Bowie'


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


def test_unrecognized_arguments_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', '--foo', 'h2x', ''])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert 'unrecognized arguments: --foo' in err


def test_invalid_command_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'foo'])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert 'invalid choice: \'foo\'' in err


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


def test_h2x_should_be_accessible(capsys):
    with open(infile) as f:
        content = f.read()
    piculet.main(argv=['piculet', 'h2x', infile])
    out, err = capsys.readouterr()
    assert out == content


def test_h2x_should_use_stdin_when_input_is_dash(capsys):
    with open(infile) as f:
        content = f.read()
    with patch('sys.stdin', StringIO(content)):
        piculet.main(argv=['piculet', 'h2x', '-'])
    out, err = capsys.readouterr()
    assert out == content


def test_scrape_no_url_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'scrape', '-s', '', '-r', ''])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert 'following arguments are required: url' in err


def test_scrape_no_spec_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'scrape', '', '-r', ''])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert 'following arguments are required: -s' in err


def test_scrape_missing_spec_file_should_fail_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'scrape', wikipedia_bowie, '-s', '', '-r', ''])
    out, err = capsys.readouterr()
    assert 'No such file or directory: ' in err


def test_scrape_unknown_scraper_should_fail_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'scrape', wikipedia_bowie, '-s', wikipedia_spec,
                           '-r', 'foo'])
    out, err = capsys.readouterr()
    assert 'Rules not found: ' in err


def test_scrape_no_rules_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'scrape', '', '-s', ''])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert 'following arguments are required: -r' in err


@mark.skipif(not test_config.getvalue('--cov'), reason='makes URL retrieval')
def test_scrape_should_be_accessible(capsys):
    piculet.main(argv=['piculet', 'scrape', wikipedia_bowie, '-s', wikipedia_spec,
                       '-r', 'person', '--html'])
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert data['name'] == 'David Bowie'
