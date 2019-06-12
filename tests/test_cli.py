import pytest
from unittest import mock

import json
from io import StringIO
from tempfile import gettempdir

from pathstring import Path
from pkg_resources import get_distribution

import piculet


movie_spec = Path(__file__).parent.parent.joinpath("examples", "movie.json")

tempdir = Path("/dev/shm")
if not tempdir.exists():
    tempdir = Path(gettempdir())


def test_help_should_print_usage_and_exit(capsys):
    with pytest.raises(SystemExit):
        piculet.main(argv=["piculet", "--help"])
    out, err = capsys.readouterr()
    assert out.startswith("usage: ")


def test_version_should_print_version_number_and_exit(capsys):
    with pytest.raises(SystemExit):
        piculet.main(argv=["piculet", "--version"])
    out, err = capsys.readouterr()
    assert "piculet " + get_distribution("piculet").version + "\n" in {out, err}


def test_if_given_no_command_should_print_usage_and_exit(capsys):
    with pytest.raises(SystemExit):
        piculet.main(argv=["piculet"])
    out, err = capsys.readouterr()
    assert err.startswith("usage: ")
    assert "error: one of the arguments -s/--spec --h2x is required" in err


def test_if_given_conflicting_commands_should_print_usage_and_exit(capsys):
    with pytest.raises(SystemExit):
        piculet.main(argv=["piculet", "-s", "foo.json", "--h2x"])
    out, err = capsys.readouterr()
    assert err.startswith("usage: ")
    assert "error: argument --h2x: not allowed with argument -s/--spec" in err


def test_scrape_should_print_data_extracted_from_stdin(capsys, shining_content):
    with mock.patch("sys.stdin", StringIO(shining_content)):
        piculet.main(argv=["piculet", "-s", movie_spec])
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert data["title"] == "The Shining"


def test_scrape_should_honor_html_setting(capsys, shining_content):
    content = shining_content.replace('<meta charset="utf-8"/>', '<meta charset="utf-8">')
    with mock.patch("sys.stdin", StringIO(content)):
        piculet.main(argv=["piculet", "-s", movie_spec, "--html"])
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert data["title"] == "The Shining"


def test_h2x_should_convert_document_from_stdin(capsys):
    with mock.patch("sys.stdin", StringIO("<img>")):
        piculet.main(argv=["piculet", "--h2x"])
    out, err = capsys.readouterr()
    assert out == "<img/>"
