from pytest import fixture

from subprocess import Popen
from time import sleep

import os


@fixture(scope='session')
def web_server(request):
    """Address of local web server for serving test files."""
    port = 2016

    command = ['python3', '-m', 'http.server', str(port), '--bind', '127.0.0.1']
    process = Popen(command, cwd=os.path.dirname(__file__))
    sleep(0.5)

    def finalize():
        process.kill()

    request.addfinalizer(finalize)
    return 'http://127.0.0.1:{}/files'.format(port)


@fixture(autouse=True)
def web_cache():
    """Environment variable for web cache directory."""
    os.environ['WOODY_WEB_CACHE_DIR'] = os.path.join(os.path.dirname(__file__),
                                                     '.cache')
