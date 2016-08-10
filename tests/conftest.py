from pytest import fixture

import os


@fixture(scope='session', autouse=True)
def web_cache():
    """Environment variable for web cache directory."""
    os.environ['WOODY_WEB_CACHE'] = os.path.join(os.path.dirname(__file__), '.cache')


@fixture(scope='session', params=['0', '1'], autouse=True)
def lxml(request):
    os.environ['WOODY_USE_LXML'] = request.param
