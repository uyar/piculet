from pytest import fixture

from pathlib import Path

import piculet


@fixture(scope="session")
def shining_content():
    """Contents of the test file for the movie "The Shining"."""
    examples_dir = Path(__file__).parent.parent / "examples"
    return examples_dir.joinpath("shining.html").read_text()


@fixture
def shining(shining_content):
    """Root element of the test XML tree for the movie "The Shining"."""
    return piculet.build_tree(shining_content)
