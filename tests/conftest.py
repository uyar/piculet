from __future__ import absolute_import, division, print_function, unicode_literals

from pytest import fixture

import piculet

import logging
import os
import socket


logging.raiseExceptions = False


cache_dir = os.path.join(os.path.dirname(__file__), '.cache')
os.environ['PICULET_WEB_CACHE'] = cache_dir
# os.environ['HTTPS_PROXY'] = 'http://localhost:8123'

enabled_socket = socket.socket


TEST_PAGES = {
    'bowie': 'https://en.wikipedia.org/wiki/David_Bowie'
}


for page in TEST_PAGES.values():
    piculet.get_document(page)


@fixture(scope='session')
def test_pages():
    """Addresses and cache locations of test pages."""
    return {k: (v, os.path.join(cache_dir, piculet.get_hash(v)))
            for k, v in TEST_PAGES.items()}


@fixture(scope='session', autouse=True)
def disable_internet(request):
    """Disable Internet access."""

    def disabled_socket(*args, **kwargs):
        raise RuntimeError('Internet access disabled')

    old_socket = socket.socket
    socket.socket = disabled_socket
    yield
    socket.socket = old_socket


@fixture(scope='function')
def enable_internet(request):
    """Enable Internet access."""
    old_socket = socket.socket
    socket.socket = enabled_socket
    yield
    socket.socket = old_socket
