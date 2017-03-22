from pytest import fixture, raises
from unittest.mock import patch

from io import StringIO

import logging
import os

import piculet


@fixture(scope='module', autouse=True)
def logging_no_exceptions():
    """Fixture for preventing logging exceptions."""
    logging.raiseExceptions = False


def test_no_arguments_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet'])
    out, err = capsys.readouterr()
    assert out.startswith('usage: ')


def test_help_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', '--help'])
    out, err = capsys.readouterr()
    assert out.startswith('usage: ')


def test_unrecognized_arguments_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', '--foo'])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert 'unrecognized arguments: --foo' in err


def test_unknown_command_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'foo'])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert 'invalid choice: \'foo\'' in err


def test_debug_mode_should_print_debug_messages_on_stderr(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', '--debug'])
    out, err = capsys.readouterr()
    assert 'running in debug mode' in err


def test_h2x_no_input_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'h2x'])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert 'following arguments are required: file' in err


def test_h2x_should_be_accessible(capsys):
    infile = os.path.join(os.path.dirname(__file__), 'files', 'utf-8_charset_utf-8.html')
    with open(infile) as f:
        content = f.read()
    piculet.main(argv=['piculet', 'h2x', infile])
    out, err = capsys.readouterr()
    assert out == content


def test_h2x_should_use_stdin_when_dash_input(capsys):
    infile = os.path.join(os.path.dirname(__file__), 'files', 'utf-8_charset_utf-8.html')
    with open(infile) as f:
        content = f.read()
    with patch('sys.stdin', StringIO(content)):
        piculet.main(argv=['piculet', 'h2x', '-'])
    out, err = capsys.readouterr()
    assert out == content
