import json
import subprocess

import piculet


def test_help_should_print_usage_and_exit(capfd):
    subprocess.run(["piculet", "--help"])
    std = capfd.readouterr()
    assert std.out.startswith("usage: ")


def test_version_should_print_version_number_and_exit(capfd):
    subprocess.run(["piculet", "--version"])
    std = capfd.readouterr()
    assert std.out == f"{piculet.__version__}\n"


def test_if_given_no_spec_should_print_usage_and_exit(capfd):
    subprocess.run(["piculet"])
    std = capfd.readouterr()
    assert std.err.startswith("usage: ")
    assert "error: the following arguments are required: -s/--spec" in std.err


def test_scrape_should_print_data_extracted_from_stdin(capfd, shining_file, movie_spec):
    cat = subprocess.run(["cat", shining_file], check=True, capture_output=True)
    subprocess.run(["piculet", "-s", movie_spec], input=cat.stdout)
    std = capfd.readouterr()
    data = json.loads(std.out)
    assert data["title"] == "The Shining"


def test_scrape_should_honor_html_setting(capfd, shining_content, movie_spec):
    content = shining_content.replace('<meta charset="utf-8"/>', '<meta charset="utf-8">')
    echo = subprocess.run(["echo", content], check=True, capture_output=True)
    subprocess.run(["piculet", "-s", movie_spec, "--html"], input=echo.stdout)
    std = capfd.readouterr()
    data = json.loads(std.out)
    assert data["title"] == "The Shining"
