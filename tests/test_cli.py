import json
import subprocess


def test_if_given_no_spec_should_print_usage_and_exit(capfd):
    subprocess.run(["piculet"])
    std = capfd.readouterr()
    assert std.err.startswith("usage: ")
    assert "error: the following arguments are required: -s/--spec" in std.err


def test_scrape_should_print_data_extracted_from_file(capfd, examples):
    subprocess.run(["piculet", "-s", examples.movie_spec, examples.shining_doc])
    std = capfd.readouterr()
    data = json.loads(std.out)
    assert data["title"] == "The Shining"


def test_scrape_should_print_data_extracted_from_stdin(capfd, examples):
    echo = subprocess.run(["echo", examples.shining_content], check=True, capture_output=True)
    subprocess.run(["piculet", "-s", examples.movie_spec], input=echo.stdout)
    std = capfd.readouterr()
    data = json.loads(std.out)
    assert data["title"] == "The Shining"


def test_scrape_should_honor_html_setting(capfd, examples):
    content = examples.shining_content.replace('<meta charset="utf-8"/>', '<meta charset="utf-8">')
    echo = subprocess.run(["echo", content], check=True, capture_output=True)
    subprocess.run(["piculet", "-s", examples.movie_spec, "--html"], input=echo.stdout)
    std = capfd.readouterr()
    data = json.loads(std.out)
    assert data["title"] == "The Shining"
