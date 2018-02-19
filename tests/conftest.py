from __future__ import absolute_import, division, print_function, unicode_literals

from pytest import fixture

import logging
import os
import sys
from hashlib import md5
from io import BytesIO

import piculet


PY2 = sys.version_info < (3, 0)


if PY2:
    import mock
else:
    from unittest import mock

if PY2:
    from urllib2 import urlopen
else:
    from urllib.request import urlopen


logging.raiseExceptions = False


cache_dir = os.path.join(os.path.dirname(__file__), '.cache')
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)


def mock_urlopen(url):
    key = md5(url.encode('utf-8')).hexdigest()
    cache_file = os.path.join(cache_dir, key)
    if not os.path.exists(cache_file):
        content = urlopen(url).read()
        with open(cache_file, 'wb') as f:
            f.write(content)
    else:
        with open(cache_file, 'rb') as f:
            content = f.read()
    return BytesIO(content)


piculet.urlopen = mock.Mock(wraps=mock_urlopen)


@fixture(scope='session')
def shining_content():
    """Contents of the shining.html file."""
    file_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'shining.html')
    with open(file_path) as f:
        content = f.read()
    return content


@fixture
def shining(shining_content):
    """Root element of the XML tree for the movie document "The Shining"."""
    return piculet.build_tree(shining_content)
