import pytest

from pathlib import Path

import piculet


cache_dir = Path(__file__).parent / ".cache"
cache_dir.mkdir(exist_ok=True)

examples_dir = Path(__file__).parent.parent / "examples"


@pytest.fixture(scope="session")
def movie_spec():
    """Path of the spec file movies."""
    return examples_dir / "movie.json"


@pytest.fixture(scope="session")
def shining_file():
    """Path of the test file for the movie "The Shining"."""
    return examples_dir / "shining.html"


@pytest.fixture(scope="session")
def shining_content(shining_file):
    """Contents of the test file for the movie "The Shining"."""
    return shining_file.read_text()


@pytest.fixture
def shining(shining_content):
    """Root element of the test XML tree for the movie "The Shining"."""
    return piculet.build_tree(shining_content)
