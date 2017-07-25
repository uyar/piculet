from __future__ import absolute_import, division, print_function, unicode_literals

from pytest import fixture

import logging
import os
from hashlib import md5
from io import BytesIO

import piculet


if not piculet.PY33:
    import mock
else:
    from unittest import mock


logging.raiseExceptions = False


cache_dir = os.path.join(os.path.dirname(__file__), '.cache')
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)


def get_cache_file(url):
    key = md5(url.encode('utf-8')).hexdigest()
    return os.path.join(cache_dir, key)


def cache_document(url):
    cache_file = get_cache_file(url)
    if not os.path.exists(cache_file):
        content = piculet.urlopen(url).read()
        with open(cache_file, 'wb') as f:
            f.write(content)


def mock_urlopen(url):
    cache_file = get_cache_file(url)
    with open(cache_file, 'rb') as f:
        content = f.read()
    return BytesIO(content)


@fixture(scope='session', autouse=True)
def setup_cache():
    cache_document('https://en.wikipedia.org/wiki/David_Bowie')
    piculet.urlopen = mock.Mock(wraps=mock_urlopen)
    yield
