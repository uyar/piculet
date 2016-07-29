from pytest import fixture, mark, raises

import os
import time

from woody import scrape


@fixture(scope='session')
def dummy_spec():
    """Dummy data extraction spec."""
    return [{
        'id': 'dummy',
        'url': 'http://en.wikipedia.org/',
        'rules': []
    }]


@mark.skip
def test_scrape_url_uncached_should_retrieve_from_web(dummy_spec):
    del os.environ['WOODY_WEB_CACHE_DIR']
    start = time.time()
    scrape(dummy_spec, 'dummy')
    end = time.time()
    assert end - start > 1


def test_scrape_url_cached_should_read_from_disk(dummy_spec):
    # FIXME: make sure that the URL is already in cache
    start = time.time()
    scrape(dummy_spec, 'dummy')
    end = time.time()
    assert end - start < 1


def test_scrape_url_multiple_ids_should_raise_error(dummy_spec):
    dummy_spec.append(dummy_spec[0])
    with raises(ValueError):
        scrape(dummy_spec, 'dummy')
