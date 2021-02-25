import pytest
from unittest import mock

import os
from hashlib import md5
from io import BytesIO
from urllib.request import urlopen

import piculet


cache_dir = os.path.join(os.path.dirname(__file__), ".cache")
os.makedirs(cache_dir, exist_ok=True)


def mock_urlopen(url):
    url_key = md5(url.encode("utf-8")).hexdigest()
    cache_file = os.path.join(cache_dir, url_key)
    if cache_file.exists():
        content = cache_file.read_bytes()
    else:
        with urlopen(url) as connection:
            content = connection.read()
        cache_file.write_bytes(content)
    return BytesIO(content)


piculet.urlopen = mock.Mock(wraps=mock_urlopen)


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
