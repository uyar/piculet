from pytest import fixture
from unittest import mock

from hashlib import md5
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

import piculet


cache_dir = Path(__file__).with_name(".cache")
cache_dir.mkdir(exist_ok=True)


def mock_urlopen(url):
    url_key = md5(url.encode("utf-8")).hexdigest()
    cache_file = Path(cache_dir, url_key)
    if cache_file.exists():
        content = cache_file.read_bytes()
    else:
        content = urlopen(url).read()
        cache_file.write_bytes(content)
    return BytesIO(content)


piculet.urlopen = mock.Mock(wraps=mock_urlopen)


@fixture(scope="session")
def shining_content():
    """Contents of the shining.html file."""
    path = Path(__file__).parent.parent.joinpath("examples", "shining.html")
    return path.read_text(encoding="utf-8")


@fixture
def shining(shining_content):
    """Root element of the XML tree for the movie document "The Shining"."""
    return piculet.build_tree(shining_content)
