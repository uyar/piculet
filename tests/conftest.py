from pytest import fixture

import os


@fixture(scope='session', autouse=True)
def web_cache():
    """Environment variable for web cache directory."""
    os.environ['PICULET_WEB_CACHE'] = os.path.join(os.path.dirname(__file__), '.cache')
