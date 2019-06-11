from pytest import config, mark, raises

import json
import sys
from io import StringIO
from pathlib import Path

from pkg_resources import get_distribution

import piculet


if sys.version_info.major < 3:
    import mock
else:
    from unittest import mock


wikipedia_spec = Path(__file__).parent.parent.joinpath("examples", "wikipedia.json")


def test_version():
    assert get_distribution("piculet").version == piculet.__version__


def test_help_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=["piculet", "--help"])
    out, err = capsys.readouterr()
    assert out.startswith("usage: ")


def test_version_should_print_version_number_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=["piculet", "--version"])
    out, err = capsys.readouterr()
    assert "piculet " + get_distribution("piculet").version + "\n" in {out, err}


def test_no_command_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=["piculet"])
    out, err = capsys.readouterr()
    assert err.startswith("usage: ")
    assert ("required: command" in err) or ("too few arguments" in err)


def test_invalid_command_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=["piculet", "foo"])
    out, err = capsys.readouterr()
    assert err.startswith("usage: ")
    assert ("invalid choice: 'foo'" in err) or ("invalid choice: u'foo'" in err)


def test_unrecognized_arguments_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=["piculet", "--foo", "h2x", ""])
    out, err = capsys.readouterr()
    assert err.startswith("usage: ")
    assert "unrecognized arguments: --foo" in err


def test_h2x_no_input_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=["piculet", "h2x"])
    out, err = capsys.readouterr()
    assert err.startswith("usage: ")
    assert ("required: file" in err) or ("too few arguments" in err)


@mark.skipif(sys.platform not in {"linux", "linux2"}, reason="/dev/shm only available on linux")
def test_h2x_should_read_given_file(capsys):
    content = "<html></html>"
    path = Path("/dev/shm/test.html")
    path.write_text(content, encoding="utf-8")
    piculet.main(argv=["piculet", "h2x", "/dev/shm/test.html"])
    out, err = capsys.readouterr()
    path.unlink()
    assert out == content


def test_h2x_should_read_stdin_when_input_is_dash(capsys):
    content = "<html></html>"
    with mock.patch("sys.stdin", StringIO(content)):
        piculet.main(argv=["piculet", "h2x", "-"])
    out, err = capsys.readouterr()
    assert out == content


def test_scrape_no_url_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=["piculet", "scrape", "-s", str(wikipedia_spec)])
    out, err = capsys.readouterr()
    assert err.startswith("usage: ")
    assert ("required: document" in err) or ("too few arguments" in err)


def test_scrape_no_spec_should_print_usage_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=["piculet", "scrape", "http://www.foo.com/"])
    out, err = capsys.readouterr()
    assert err.startswith("usage: ")
    assert ("required: -s" in err) or ("--spec is required" in err)


def test_scrape_missing_spec_file_should_fail_and_exit(capsys):
    with raises(SystemExit):
        piculet.main(argv=["piculet", "scrape", "http://www.foo.com/", "-s", "foo.json"])
    out, err = capsys.readouterr()
    assert "No such file or directory: " in err


def test_scrape_local_should_scrape_given_file(capsys):
    dirpath = Path(__file__).parent.parent.joinpath("examples")
    shining = Path(dirpath, "shining.html")
    spec = Path(dirpath, "movie.json")
    piculet.main(argv=["piculet", "scrape", str(shining), "-s", str(spec)])
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert data["title"] == "The Shining"


@mark.skipif(not config.getvalue("--cov"), reason="takes unforeseen amount of time")
def test_scrape_should_scrape_given_url(capsys):
    piculet.main(
        argv=[
            "piculet",
            "scrape",
            "https://en.wikipedia.org/wiki/David_Bowie",
            "-s",
            str(wikipedia_spec),
            "--html",
        ]
    )
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert data["name"] == "David Bowie"
