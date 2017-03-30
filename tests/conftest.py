from pytest import fixture

import logging
import os
import socket


logging.raiseExceptions = False

os.environ['PICULET_WEB_CACHE'] = os.path.join(os.path.dirname(__file__), '.cache')


@fixture(scope='function')
def disable_internet(request):
    """Disable Internet access."""

    def guard(*args, **kwargs):
        raise RuntimeError('Internet access disabled')

    old_socket = socket.socket
    socket.socket = guard
    yield
    socket.socket = old_socket
