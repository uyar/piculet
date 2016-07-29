from pytest import fixture

import json
import os
import re

from woody import scrape


@fixture(scope='session')
def imdb_spec():
    """Data extraction spec for the IMDb site."""
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
        'manos': 60666,             # Manos: The Hands of Fate (Bottom 100)
        'ace_in_the_hole': 43338,   # Ace in the Hole
        'matrix_tv': 389150,        # The Matrix Defence (TV movie, no poster)
        'ates_parcasi': 1863157     # Ateş Parçası (no rating, votes, rank, plot, keywords)
    }


def test_long_title_should_have_title_and_year(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix'])
    assert data['long title'] == 'The Matrix (1999)'


def test_poster_exists_should_have_url(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix'])
    assert data['poster'].endswith('._V1._SX94_SY140_.jpg')


def test_poster_none_should_have_no_url(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix_tv'])
    assert 'poster' not in data


def test_rating_exists_should_match(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix'])
    assert re.match(r'^[1-9]\.\d\/10$', data['rating'])


def test_rating_none_should_have_no_rating(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['ates_parcasi'])
    assert 'rating' not in data


def test_votes_exists_should_match(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix'])
    assert re.match(r'^[1-9][0-9,]* votes$', data['votes'])


def test_votes_none_should_have_no_votes(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['ates_parcasi'])
    assert 'votes' not in data


def test_rank_top250_should_match(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix'])
    assert re.match(r'^Top 250: #\d+$', data['rank'])


def test_rank_bottom100_should_match(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['manos'])
    assert re.match(r'^Bottom 100: #\d+$', data['rank'])


def test_rank_none_should_have_no_rank(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['ace_in_the_hole'])
    assert 'rank' not in data
