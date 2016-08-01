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
        'ace_in_the_hole': 43338,    # Ace in the Hole
        'ates_parcasi': 1863157,     # Ateş Parçası (no rating, votes, rank, plot, keywords)
        'band_of_brothers': 185906,  # Band of Brothers (mini-series, ended)
        'dr_who': 436992,            # Doctor Who 2005 (TV series)
        'dr_who_blink': 1000252,     # Doctor Who 2005: Blink (TV episode)
        'manos': 60666,              # Manos: The Hands of Fate (Bottom 100)
        'matrix': 133093,            # The Matrix (top 250)
        'matrix_tv': 389150,         # The Matrix Defence (TV movie, no poster)
        'matrix_vg': 390244,         # The Matrix Online (video game)
        'matrix_video': 109151,      # Armitage III: Poly Matrix (video movie)
        'roast_sheen': 1985970       # Comedy Central Roast of Charlie Sheen (TV Special)
    }


def test_long_title_should_have_title_and_year(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix'])
    assert data['long title'] == 'The Matrix (1999)'


def test_long_title_video_should_have_type(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix_video'])
    assert data['long title'] == 'Armitage III: Poly Matrix (1996) (V)'


def test_long_title_tv_movie_should_have_type(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix_tv'])
    assert data['long title'] == 'The Matrix Defence (2003) (TV)'


def test_long_title_tv_series_should_have_quotes_but_no_type(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['dr_who'])
    assert data['long title'] == '"Doctor Who" (2005)'


def test_long_title_tv_mini_series_should_have_quotes_but_no_type(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['band_of_brothers'])
    assert data['long title'] == '"Band of Brothers" (2001)'


def test_long_title_tv_episode_should_have_series_title(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['dr_who_blink'])
    assert data['long title'] == '"Doctor Who" Blink (2007)'


def test_long_title_video_game_should_have_type(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix_vg'])
    assert data['long title'] == 'The Matrix Online (2005) (VG)'


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


def test_genres_single_without_see_more_should_have_one(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['ates_parcasi'])
    assert data['genre'] == 'Comedy'


def test_genres_single_with_see_more_should_have_see_more(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['roast_sheen'])
    assert data['genre'] == 'Comedy See more »'


# TODO: find an entry with multiple genres but not see more
# def test_genres_multiple_without_see_more_should_match(imdb_spec, movie_ids):
#     data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['???'])
#     assert '???' not in data


def test_genres_multiple_with_see_more_should_have_see_more(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix'])
    assert data['genre'] == 'Action | Sci-Fi See more »'


# TODO: find an entry without a genre
# def test_genres_none_should_have_no_genres(imdb_spec, movie_ids):
#     data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['???'])
#     assert 'Genre:' not in data
