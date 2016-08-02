from pytest import fixture

import json
import os
import re

from woody import scrape


@fixture(scope='session')
def imdb():
    """Data extraction spec for the IMDb site."""
    cwd = os.path.dirname(__file__)
    specfile = os.path.join(cwd, '..', 'examples', 'imdb.json')
    with open(specfile) as f:
        spec = json.loads(f.read())
    return spec


@fixture(scope='session')
def movies():
    """The IMDb movie ids."""
    return {
        'ace_in_the_hole': 43338,       # multiple languages
        'ates_parcasi': 1863157,        # no poster, rating, votes, rank, plot, keywords
        'band_of_brothers': 185906,     # mini-series, ended
        'dr_who': 436992,               # TV series, continuing
        'dr_who_blink': 1000252,        # TV episode
        'house_md': 412142,             # TV series, ended
        'if': 63850,                    # one tagline
        'manos': 60666,                 # bottom 100
        'matrix': 133093,               # top 250
        'matrix_short': 2971344,        # short movie, language none
        'matrix_tv': 389150,            # TV movie
        'matrix_tv_short': 274085,      # TV short movie
        'matrix_vg': 390244,            # video game, no runtime
        'matrix_video': 109151,         # video movie
        'roast_sheen': 1985970,         # TV Special
        'shining': 81505,               # runtimes with multiple notes
        'suspiria': 76786               # runtimes in different countries
    }


def test_long_title_should_have_title_and_year(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['long title'] == 'The Matrix (1999)'


def test_long_title_video_movie_should_include_type(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_video'])
    assert data['long title'] == 'Armitage III: Poly Matrix (1996) (V)'


def test_long_title_tv_movie_should_include_type(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_tv'])
    assert data['long title'] == 'The Matrix Defence (2003) (TV)'


def test_long_title_video_game_should_include_type(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_vg'])
    assert data['long title'] == 'The Matrix Online (2005) (VG)'


def test_long_title_tv_series_should_have_quotes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who'])
    assert data['long title'] == '"Doctor Who" (2005)'


def test_long_title_tv_mini_series_should_have_quotes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['band_of_brothers'])
    assert data['long title'] == '"Band of Brothers" (2001)'


def test_long_title_tv_episode_should_have_series_title_in_quotes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who_blink'])
    assert data['long title'] == '"Doctor Who" Blink (2007)'


def test_poster_should_have_url(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['poster'].endswith('._V1._SX94_SY140_.jpg')


def test_poster_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'poster' not in data


def test_rating_should_be_a_decimal_over_10(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert re.match(r'^[1-9]\.\d\/10$', data['rating'])


def test_rating_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'rating' not in data


def test_votes_should_be_a_thousands_separated_number(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert re.match(r'^[1-9][0-9,]* votes$', data['votes'])


def test_votes_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'votes' not in data


def test_rank_top250_should_include_position_number(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert re.match(r'^Top 250: #\d+$', data['rank'])


def test_rank_bottom100_should_include_position_number(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['manos'])
    assert re.match(r'^Bottom 100: #\d+$', data['rank'])


def test_rank_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'rank' not in data


def test_genre_one_without_see_more_should_be_a_single_genre(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert data['genre'] == 'Comedy'


def test_genre_one_with_see_more_should_end_in_see_more(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['roast_sheen'])
    assert data['genre'] == 'Comedy See more »'


def test_genre_many_without_see_more_should_be_pipe_separated(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_tv_short'])
    assert data['genre'] == 'Comedy | Short'


def test_genres_many_with_see_more_should_end_in_see_more(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['genre'] == 'Action | Sci-Fi See more »'


# TODO: find an entry without a genre
# def test_genre_none_should_be_excluded(imdb, movies):
#     data = scrape(imdb, 'movie_combined_details', imdb_id=movies['???'])
#     assert 'genre' not in data


def test_tagline_without_see_more_should_be_a_single_tagline(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['if'])
    assert data['tagline'] == 'Which side will you be on?'


def test_tagline_with_see_more_should_end_in_see_more(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['tagline'] == 'Free your mind See more »'


def test_tagline_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who_blink'])
    assert 'tagline' not in data


def test_plot_with_summary_and_synopsis_should_end_in_summary_and_synopsis(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['plot'].startswith('A computer hacker learns ')
    assert data['plot'].endswith('Full summary » | Full synopsis »')


def test_plot_with_summary_should_end_in_summary(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who'])
    assert data['plot'].startswith('The further adventures of ')
    assert data['plot'].endswith('Full summary »')


def test_plot_no_synopsis_should_end_in_add_synopsis(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_tv_short'])
    assert data['plot'].endswith(' | Add synopsis »')


def test_plot_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'plot' not in data


def test_runtime_one_should_be_a_number_in_minutes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['runtime'] == '136 min'


# TODO: find an entry with one runtime and notes
# def test_runtime_one_with_notes_should_include_notes(imdb, movies):
#     data = scrape(imdb, 'movie_combined_details', imdb_id=movies['???'])
#     assert data['runtime'] == '??? min (???)'


def test_runtime_many_with_notes_should_be_pipe_separated(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['house_md'])
    assert data['runtime'] == '44 min | 7788 min (Entire series)'


def test_runtime_many_with_multiple_notes_should_include_all_notes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['shining'])
    assert data['runtime'] == '144 min (cut) | 119 min (cut) (European version)' \
                              ' | 146 min (original version)'


def test_runtime_many_with_different_countries_should_include_all_countries(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['suspiria'])
    assert data['runtime'] == '98 min | Germany:88 min | USA:92 min | Argentina:95 min'


def test_runtime_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_vg'])
    assert 'runtime' not in data


def test_country_one_should_be_a_country_name(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who_blink'])
    assert data['country'] == 'UK'


def test_country_many_should_be_pipe_separated(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who'])
    assert data['country'] == 'UK | Canada'


# TODO: find an entry with no country
# def test_country_none_should_be_excluded(imdb, movies):
#     data = scrape(imdb, 'movie_combined_details', imdb_id=movies['???'])
#     assert 'country' not in data


def test_language_one_should_be_a_language_name(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who_blink'])
    assert data['language'] == 'English'


def test_language_many_should_be_pipe_separated(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ace_in_the_hole'])
    assert data['language'] == 'English | Spanish | Latin'


def test_language_none_is_a_language_name(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_short'])
    assert data['language'] == 'None'


# TODO: find an entry without a language
# def test_language_none_should_be_excluded(imdb, movies):
#     data = scrape(imdb, 'movie_combined_details', imdb_id=movies['???'])
#     assert 'language' not in data
