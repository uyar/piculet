import json
import subprocess
from pathlib import Path


examples_dir = Path(__file__).parent.parent / "examples"
movie_spec = examples_dir / "movie.json"
movie_doc = examples_dir / "shining.html"


def test_if_given_no_spec_should_print_usage_and_exit(capfd):
    subprocess.run(["piculet"])
    std = capfd.readouterr()
    assert std.err.startswith("usage: ")
    assert "error: the following arguments are required: -s/--spec" in std.err


def test_scrape_should_print_data_extracted_from_stdin(capfd):
    content = movie_doc.read_text()
    echo = subprocess.run(["echo", content], check=True, capture_output=True)
    subprocess.run(["piculet", "-s", movie_spec], input=echo.stdout)
    std = capfd.readouterr()
    data = json.loads(std.out)
    assert data["title"] == "The Shining"


def test_scrape_should_honor_html_setting(capfd):
    content = movie_doc.read_text().replace('<meta charset="utf-8"/>', '<meta charset="utf-8">')
    echo = subprocess.run(["echo", content], check=True, capture_output=True)
    subprocess.run(["piculet", "-s", movie_spec, "--html"], input=echo.stdout)
    std = capfd.readouterr()
    data = json.loads(std.out)
    assert data["title"] == "The Shining"
