from pytest import fixture

import logging
import os
import socket


logging.raiseExceptions = False

os.environ['PICULET_WEB_CACHE'] = os.path.join(os.path.dirname(__file__), '.cache')

enabled_socket = socket.socket


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
