from __future__ import absolute_import, division, print_function, unicode_literals

from pytest import config, mark, raises

import json
import logging
import os
import sys
from io import StringIO

from pkg_resources import get_distribution

import piculet


if sys.version_info.major < 3:
    import mock
else:
    from unittest import mock


base_dir = os.path.dirname(__file__)
wikipedia_spec = os.path.join(base_dir, '..', 'examples', 'wikipedia.json')


def test_help_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', '--help'])
    out, err = capsys.readouterr()
    assert out.startswith('usage: ')


def test_version_should_print_version_number_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', '--version'])
    out, err = capsys.readouterr()
    assert 'piculet ' + get_distribution('piculet').version + '\n' in {out, err}


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


def test_debug_mode_should_print_debug_messages(caplog):
    caplog.set_level(logging.DEBUG)
    with mock.patch('sys.stdin', StringIO('<html></html>')):
        piculet.main(argv=['piculet', '--debug', 'h2x', '-'])
    assert caplog.record_tuples[0][-1] == 'running in debug mode'


def test_h2x_no_input_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'h2x'])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert ('required: file' in err) or ('too few arguments' in err)


@mark.skipif(sys.platform not in {'linux', 'linux2'},
             reason='/dev/shm only available on linux')
def test_h2x_should_read_given_file(capsys):
    content = '<html></html>'
    with open('/dev/shm/test.html', 'w') as f:
        f.write(content)
    piculet.main(argv=['piculet', 'h2x', '/dev/shm/test.html'])
    out, err = capsys.readouterr()
    os.unlink('/dev/shm/test.html')
    assert out == content


def test_h2x_should_read_stdin_when_input_is_dash(capsys):
    content = '<html></html>'
    with mock.patch('sys.stdin', StringIO(content)):
        piculet.main(argv=['piculet', 'h2x', '-'])
    out, err = capsys.readouterr()
    assert out == content


def test_scrape_no_url_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'scrape', '-s', wikipedia_spec])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert ('required: document' in err) or ('too few arguments' in err)


def test_scrape_no_spec_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'scrape', 'http://www.foo.com/'])
    out, err = capsys.readouterr()
    assert err.startswith('usage: ')
    assert ('required: -s' in err) or ('--spec is required' in err)


def test_scrape_missing_spec_file_should_fail_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=['piculet', 'scrape', 'http://www.foo.com/', '-s', 'foo.json'])
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


@mark.skipif(not config.getvalue('--cov'),
             reason='takes unforeseen amount of time')
def test_scrape_should_scrape_given_url(capsys):
    piculet.main(argv=['piculet', 'scrape', 'https://en.wikipedia.org/wiki/David_Bowie',
                       '-s', wikipedia_spec, '--html'])
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert data['name'] == 'David Bowie'
