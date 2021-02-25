import pytest

import os

import piculet


cache_dir = os.path.join(os.path.dirname(__file__), ".cache")
os.makedirs(cache_dir, exist_ok=True)


@pytest.fixture(scope="session")
def shining_content():
    """Contents of the test file for the movie "The Shining"."""
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "shining.html")
    with open(path, encoding="utf-8") as f:
        content = f.read()
    return content


@pytest.fixture
def shining(shining_content):
    """Root element of the test XML tree for the movie "The Shining"."""
    return piculet.build_tree(shining_content)
