from pytest import fixture

import json
import os
import re

from woody.wood import scrape_url


os.environ['WOODY_WEB_CACHE_DIR'] = os.path.join(os.path.dirname(__file__), '.cache')


@fixture(scope='session')
def imdb_spec():
    """Data extraction spec for the IMDb site (in JSON format)."""
    cwd = os.path.dirname(__file__)
    specfile = os.path.join(cwd, '..', 'examples', 'imdb.json')
    with open(specfile) as f:
        spec = json.loads(f.read())
    return spec


@fixture(scope='session')
def movie_ids():
    """The IMDb movie ids."""
    return {
        'matrix': 133093,           # The Matrix (top 250)
        'matrix_tv': 389150,        # The Matrix Defence (TV movie, no poster)
        'ates_parcasi': 1863157     # Ateş Parçası (no rating, votes, rank, plot, keywords)
    }


def test_long_title_should_have_title_and_year(imdb_spec, movie_ids):
    data = scrape_url(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix'])
    assert data['long title'] == 'The Matrix (1999)'


def test_poster_exists_should_have_url(imdb_spec, movie_ids):
    data = scrape_url(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix'])
    assert data['poster'].endswith('._V1._SX94_SY140_.jpg')


def test_poster_none_should_have_no_url(imdb_spec, movie_ids):
    data = scrape_url(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix_tv'])
    assert 'poster' not in data


def test_rating_exists_should_match(imdb_spec, movie_ids):
    data = scrape_url(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix'])
    assert re.match(r'[1-9]\.\d\/10', data['rating'])


def test_rating_none_should_have_no_rating(imdb_spec, movie_ids):
    data = scrape_url(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['ates_parcasi'])
    assert 'rating' not in data
