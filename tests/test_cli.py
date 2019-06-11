import pytest
from unittest import mock

import json
from io import StringIO
from tempfile import NamedTemporaryFile, gettempdir

from pathstring import Path
from pkg_resources import get_distribution

import piculet


coverage_mode = pytest.config.getvalue("--cov")


examples_dir = Path(__file__).parent.parent.joinpath("examples")
wikipedia_spec = Path(examples_dir, "wikipedia.json")
movie_spec = Path(examples_dir, "movie.json")
shining_html = Path(examples_dir, "shining.html")

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


def test_if_given_no_document_should_print_usage_and_exit(capsys):
    with pytest.raises(SystemExit):
        piculet.main(argv=["piculet"])
    out, err = capsys.readouterr()
    assert err.startswith("usage: ")
    assert "required: document" in err


def test_if_given_document_without_command_should_print_usage_and_exit(capsys):
    with pytest.raises(SystemExit):
        piculet.main(argv=["piculet", shining_html])
    out, err = capsys.readouterr()
    assert err.startswith("usage: ")
    assert "error: one of the arguments -s/--spec --h2x is required" in err


def test_scrape_if_given_no_document_should_print_usage_and_exit(capsys):
    with pytest.raises(SystemExit):
        piculet.main(argv=["piculet", "-s", wikipedia_spec])
    out, err = capsys.readouterr()
    assert err.startswith("usage: ")
    assert "required: document" in err


def test_scrape_if_given_missing_spec_file_should_fail_and_exit(capsys):
    with pytest.raises(SystemExit):
        piculet.main(argv=["piculet", shining_html, "-s", "foo.json"])
    out, err = capsys.readouterr()
    assert "No such file or directory: " in err


def test_scrape_if_given_file_should_print_extracted_data(capsys):
    piculet.main(argv=["piculet", shining_html, "-s", movie_spec])
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert data["title"] == "The Shining"


@pytest.mark.skipif(not coverage_mode, reason="takes unforeseen amount of time")
def test_scrape_if_given_url_should_retrieve_url(capsys):
    piculet.main(
        argv=[
            "piculet",
            "https://en.wikipedia.org/wiki/David_Bowie",
            "-s",
            wikipedia_spec,
            "--html",
        ]
    )
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert data["name"] == "David Bowie"


def test_h2x_if_given_no_document_should_print_usage_and_exit(capsys):
    with pytest.raises(SystemExit):
        piculet.main(argv=["piculet", "--h2x"])
    out, err = capsys.readouterr()
    assert err.startswith("usage: ")
    assert "required: document" in err


def test_h2x_if_given_file_should_print_converted_content(capsys):
    content = "<img>"
    f = NamedTemporaryFile(dir=tempdir, buffering=0)
    f.write(content.encode("utf-8"))
    piculet.main(argv=["piculet", "--h2x", f.name])
    out, err = capsys.readouterr()
    f.close()
    assert out == "<img />"


def test_h2x_if_given_dash_should_read_from_stdin(capsys):
    content = "<img>"
    with mock.patch("sys.stdin", StringIO(content)):
        piculet.main(argv=["piculet", "--h2x", "-"])
    out, err = capsys.readouterr()
    assert out == "<img />"
