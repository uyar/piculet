from pytest import fixture

import json
import os
import re

from woody import _get_document, scrape


@fixture(scope='module')
def imdb():
    """Data extraction spec for the IMDb site."""
    cwd = os.path.dirname(__file__)
    specfile = os.path.join(cwd, '..', 'examples', 'imdb.json')
    with open(specfile) as f:
        spec = json.loads(f.read())
    return spec


@fixture(scope='module')
def movies():
    """The IMDb movie ids."""
    return {
        'ace_in_the_hole': 43338,       # multiple languages, sound mix note
        'ates_parcasi': 1863157,        # no poster, rating, votes, ...
        'band_of_brothers': 185906,     # mini-series, ended
        'dr_who': 436992,               # TV series, continuing
        'dr_who_blink': 1000252,        # TV episode
        # 'house_md': 412142,             # TV series, ended
        'if': 63850,                    # one genre, multiple colors
        'manos': 60666,                 # bottom 100, multiple certifications
        'matrix': 133093,               # top 250
        'matrix_short': 2971344,        # short movie, language "None"
        'matrix_tv': 389150,            # TV movie, no color info
        'matrix_tv_short': 274085,      # TV short movie, no plot synopsis
        'matrix_vg': 390244,            # video game, no runtime, one certification
        'matrix_video': 109151,         # video movie
        'roast_sheen': 1985970,         # TV Special, few plot keywords
        'shining': 81505,               # multiple runtimes, multiple countries
        'suspiria': 76786               # multiple country runtimes
    }


@fixture(scope='module', autouse=True)
def get_imdb_pages(imdb, movies):
    """Store all needed pages from the IMDb in the cache."""
    for scraper in imdb['scrapers']:
        for movie_id in movies.values():
            url = imdb['base_url'] + scraper['url'].format(imdb_id=movie_id)
            _get_document(url)


def test_long_title_should_have_title_and_year(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['long_title'] == 'The Matrix (1999)'


def test_long_title_video_movie_should_include_type(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_video'])
    assert data['long_title'] == 'Armitage III: Poly Matrix (1996) (V)'


def test_long_title_tv_movie_should_include_type(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_tv'])
    assert data['long_title'] == 'The Matrix Defence (2003) (TV)'


def test_long_title_video_game_should_include_type(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_vg'])
    assert data['long_title'] == 'The Matrix Online (2005) (VG)'


def test_long_title_tv_series_should_have_quotes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who'])
    assert data['long_title'] == '"Doctor Who" (2005)'


def test_long_title_tv_mini_series_should_have_quotes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['band_of_brothers'])
    assert data['long_title'] == '"Band of Brothers" (2001)'


def test_long_title_tv_episode_should_have_series_title_in_quotes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who_blink'])
    assert data['long_title'] == '"Doctor Who" Blink (2007)'


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


def test_genre_should_be_a_genre_name(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['if'])
    # if there are plot keywords there is a see more link to that page
    assert data['genre'] == 'Drama See more »'


def test_genre_many_should_be_pipe_separated(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    # if there are plot keywords there is a see more link to that page
    assert data['genre'] == 'Action | Sci-Fi See more »'


# TODO: find a movie with no genre
# def test_genre_none_should_be_excluded(imdb, movies):
#     data = scrape(imdb, 'movie_combined_details', imdb_id=movies['???'])
#     assert 'genre' not in data


def test_tagline_should_be_a_short_phrase(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    # if there is more than one tagline there is a see more link to the taglines page
    assert data['tagline'] == 'Free your mind See more »'


def test_tagline_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'tagline' not in data


def test_plot_should_end_in_full_summary(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who'])
    assert data['plot'].startswith('The further adventures of ')
    assert data['plot'].endswith('Full summary »')


def test_plot_with_synopsis_should_end_in_full_synopsis(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['plot'].startswith('A computer hacker learns ')
    assert data['plot'].endswith('Full summary » | Full synopsis »')


def test_plot_no_synopsis_should_end_in_add_synopsis(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_tv_short'])
    assert data['plot'].endswith(' | Add synopsis »')


def test_plot_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'plot' not in data


def test_plot_keywords_many_should_be_pipe_separated(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['roast_sheen'])
    assert data['plot_keywords'] == 'TV Special | Celebrity Roast'


def test_plot_keywords_many_with_see_more_should_have_see_more(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['plot_keywords'] == \
        'Computer | Hacker | Reality | Matrix | Computer Hacker See more »'


def test_plot_keywords_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'plot_keywords' not in data


def test_akas_should_be_titles(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['manos'])
    # if an aka exists there is always a see more link to the akas page
    assert data['also_known_as'] == \
        '"Манос: Руки судьбы" - Soviet Union (Russian title)' \
        ' "Manos - As Mãos do Destino" - Brazil (imdb display title) See more »'


def test_akas_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'also_known_as' not in data


def test_mpaa_should_be_a_rating(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['mpaa'] == 'Rated R for sci-fi violence and brief language'


def test_mpaa_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'mpaa' not in data


def test_runtime_should_be_a_number_in_minutes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['runtime'] == '136 min'


def test_runtime_many_should_be_pipe_separated_with_notes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['shining'])
    assert data['runtime'] == \
        '144 min (cut) | 119 min (cut) (European version) | 146 min (original version)'


def test_runtime_many_with_countries_should_include_contexts(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['suspiria'])
    assert data['runtime'] == '98 min | Germany:88 min | USA:92 min | Argentina:95 min'


def test_runtime_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_vg'])
    assert 'runtime' not in data


def test_country_should_be_a_country_name(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['country'] == 'USA'


def test_country_many_should_be_pipe_separated(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['shining'])
    assert data['country'] == 'USA | UK'


# TODO: find a movie with no country
# def test_country_none_should_be_excluded(imdb, movies):
#     data = scrape(imdb, 'movie_combined_details', imdb_id=movies['???'])
#     assert 'country' not in data


def test_language_should_be_a_language_name(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['language'] == 'English'


def test_language_many_should_be_pipe_separated(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ace_in_the_hole'])
    assert data['language'] == 'English | Spanish | Latin'


def test_language_none_is_a_language_name(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_short'])
    assert data['language'] == 'None'


# TODO: find a movie with no language
# def test_language_none_should_be_excluded(imdb, movies):
#     data = scrape(imdb, 'movie_combined_details', imdb_id=movies['???'])
#     assert 'language' not in data


def test_color_should_be_a_color_type(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['color'] == 'Color'


def test_color_with_note_should_include_note(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['manos'])
    assert data['color'] == 'Color (Eastmancolor)'


def test_color_many_should_be_pipe_separated(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['if'])
    assert data['color'] == 'Black and White | Color (Eastmancolor) (uncredited)'


def test_color_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_tv'])
    assert 'color' not in data


def test_aspect_ratio_should_be_a_number_to_one(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    # if the aspect ratio exists, there is a see more link to technical page
    assert data['aspect_ratio'] == '2.35 : 1 See more »'


def test_aspect_ratio_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'aspect_ratio' not in data


def test_sound_mix_should_be_a_sound_mix_type(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['shining'])
    assert data['sound_mix'] == 'Mono'


def test_sound_mix_with_note_should_include_note(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ace_in_the_hole'])
    assert data['sound_mix'] == 'Mono (Western Electric Recording)'


def test_sound_mix_many_should_be_pipe_separated(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['sound_mix'] == 'DTS | Dolby Digital | SDDS'


def test_sound_mix_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'sound_mix' not in data


def test_certification_should_have_context(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_vg'])
    assert data['certification'] == 'USA:T'


def test_certification_with_note_should_include_note(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who_blink'])
    assert data['certification'] == 'UK:PG (DVD rating)'


def test_certification_many_should_be_pipe_separated(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['manos'])
    assert data['certification'] == \
        'Canada:G (Quebec) (2008) | Finland:K-18 (2008) (self applied) | USA:Not Rated'


def test_certification_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'certification' not in data
