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
        'ace_in_the_hole': 43338,
        'ates_parcasi': 1863157,     # no rating, votes, rank, plot, keywords
        'band_of_brothers': 185906,  # mini-series, ended
        'dr_who': 436992,            # TV series
        'dr_who_blink': 1000252,     # TV episode
        'if': 63850,
        'manos': 60666,              # bottom 100
        'matrix': 133093,            # top 250
        'matrix_tv': 389150,         # TV movie, no poster
        'matrix_tv_short': 274085,   # TV short movie
        'matrix_vg': 390244,         # video game
        'matrix_video': 109151,      # video movie
        'roast_sheen': 1985970       # TV Special
    }


def test_long_title_should_have_title_and_year(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix'])
    assert data['long title'] == 'The Matrix (1999)'


def test_long_title_video_movie_should_have_type(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix_video'])
    assert data['long title'] == 'Armitage III: Poly Matrix (1996) (V)'


def test_long_title_tv_movie_should_have_type(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix_tv'])
    assert data['long title'] == 'The Matrix Defence (2003) (TV)'


def test_long_title_video_game_should_have_type(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix_vg'])
    assert data['long title'] == 'The Matrix Online (2005) (VG)'


def test_long_title_tv_series_should_have_quotes(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['dr_who'])
    assert data['long title'] == '"Doctor Who" (2005)'


def test_long_title_tv_mini_series_should_have_quotes(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['band_of_brothers'])
    assert data['long title'] == '"Band of Brothers" (2001)'


def test_long_title_tv_episode_should_have_series_title_in_quotes(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['dr_who_blink'])
    assert data['long title'] == '"Doctor Who" Blink (2007)'


def test_poster_should_have_url(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix'])
    assert data['poster'].endswith('._V1._SX94_SY140_.jpg')


def test_poster_none_should_be_excluded(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix_tv'])
    assert 'poster' not in data


def test_rating_should_be_a_decimal_over_10(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix'])
    assert re.match(r'^[1-9]\.\d\/10$', data['rating'])


def test_rating_none_should_be_excluded(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['ates_parcasi'])
    assert 'rating' not in data


def test_votes_should_be_a_thousands_separated_number(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix'])
    assert re.match(r'^[1-9][0-9,]* votes$', data['votes'])


def test_votes_none_should_be_excluded(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['ates_parcasi'])
    assert 'votes' not in data


def test_rank_top250_should_include_position(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix'])
    assert re.match(r'^Top 250: #\d+$', data['rank'])


def test_rank_bottom100_should_include_position(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['manos'])
    assert re.match(r'^Bottom 100: #\d+$', data['rank'])


def test_rank_none_should_be_excluded(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['ace_in_the_hole'])
    assert 'rank' not in data


def test_genre_one_without_see_more_should_be_a_single_genre(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['ates_parcasi'])
    assert data['genre'] == 'Comedy'


def test_genre_one_with_see_more_should_end_in_see_more(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['roast_sheen'])
    assert data['genre'] == 'Comedy See more »'


def test_genre_many_without_see_more_should_have_pipes(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix_tv_short'])
    assert data['genre'] == 'Comedy | Short'


def test_genres_many_with_see_more_should_end_in_see_more(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix'])
    assert data['genre'] == 'Action | Sci-Fi See more »'


# TODO: find an entry without a genre
# def test_genres_none_should_be_excluded(imdb_spec, movie_ids):
#     data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['???'])
#     assert 'genre' not in data


def test_tagline_without_see_more_should_be_a_single_tagline(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['if'])
    assert data['tagline'] == 'Which side will you be on?'


def test_tagline_with_see_more_should_end_in_see_more(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix'])
    assert data['tagline'] == 'Free your mind See more »'


def test_tagline_none_should_be_excluded(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['dr_who_blink'])
    assert 'tagline' not in data


def test_plot_with_synopsis_should_end_in_summary_and_synopsis(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix'])
    assert data['plot'].startswith('A computer hacker learns ')
    assert data['plot'].endswith('Full summary » | Full synopsis »')


def test_plot_with_summary_should_end_in_summary(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['dr_who'])
    assert data['plot'].startswith('The further adventures of ')
    assert data['plot'].endswith('Full summary »')


def test_plot_no_synopsis_should_end_in_add_synopsis(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['matrix_tv_short'])
    assert data['plot'].endswith(' | Add synopsis »')


def test_plot_none_should_be_excluded(imdb_spec, movie_ids):
    data = scrape(imdb_spec, 'movie_combined_details', imdb_id=movie_ids['ates_parcasi'])
    assert 'plot' not in data
