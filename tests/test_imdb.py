from pytest import fixture

import json
import os
import re

from piculet import _get_document, scrape


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
        'aslan': 3629794,               # no year, no director
        'ates_parcasi': 1863157,        # no poster, rating, votes, ...
        'band_of_brothers': 185906,     # mini-series, ended
        'dr_who': 436992,               # TV series, continuing
        'dr_who_blink': 1000252,        # TV episode
        'house_md': 412142,             # TV series, ended
        'house_md_first': 606035,       # first episode of House, MD
        'house_md_last': 2121965,       # last episode of House, MD
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
        'star_trek_ds9': 106145,        # TV series, multiple creators
        'suspiria': 76786,              # multiple country runtimes
        'west_side_story': 55614        # multiple directors
    }


BASE_URL = 'http://akas.imdb.com'
TITLE_BASE_URL = '{}/title/tt{{imdb_id:07}}'.format(BASE_URL)
TITLE_COMBINED_URL = '{}/combined'.format(TITLE_BASE_URL)
TITLE_KEYWORDS_URL = '{}/keywords'.format(TITLE_BASE_URL)
TITLE_TAGLINES_URL = '{}/taglines'.format(TITLE_BASE_URL)
TITLE_PLOT_SUMMARY_URL = '{}/plotsummary'.format(TITLE_BASE_URL)
TITLE_URLS = (TITLE_COMBINED_URL, TITLE_TAGLINES_URL, TITLE_PLOT_SUMMARY_URL,
              TITLE_KEYWORDS_URL)


@fixture(scope='module', autouse=True)
def get_imdb_pages(imdb, movies):
    """Store all needed pages from the IMDb in the cache."""
    for movie_id in movies.values():
        for url_template in TITLE_URLS:
            url = url_template.format(imdb_id=movie_id)
            _get_document(url)


########################################
# movie combined details page tests
########################################


MOVIE_COMBINED = 'movie_combined'


def test_movie_combined_full_title_should_have_title_and_year(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['title.full'] == 'The Matrix (1999)'


def test_movie_combined_full_title_video_movie_should_include_type(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix_video'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['title.full'] == 'Armitage III: Poly Matrix (1996) (V)'


def test_movie_combined_full_title_tv_movie_should_include_type(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix_tv'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['title.full'] == 'The Matrix Defence (2003) (TV)'


def test_movie_combined_full_title_video_game_should_include_type(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix_vg'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['title.full'] == 'The Matrix Online (2005) (VG)'


def test_movie_combined_full_title_tv_series_should_have_quotes(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['title.full'] == '"Doctor Who" (2005)'


def test_movie_combined_full_title_tv_mini_series_should_have_quotes(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['band_of_brothers'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['title.full'] == '"Band of Brothers" (2001)'


def test_movie_combined_full_title_tv_episode_should_include_series_title(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who_blink'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['title.full'] == '"Doctor Who" Blink (2007)'


def test_movie_combined_poster_should_have_link(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['poster.link'].endswith('._V1._SX94_SY140_.jpg')


def test_movie_combined_poster_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'poster.link' not in data


def test_movie_combined_title_should_not_have_year(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['title'] == 'The Matrix'


def test_movie_combined_title_video_movie_should_not_include_type(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix_video'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['title'] == 'Armitage III: Poly Matrix'


def test_movie_combined_title_tv_movie_should_not_include_type(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix_tv'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['title'] == 'The Matrix Defence'


def test_movie_combined_title_video_game_should_not_include_type(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix_vg'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['title'] == 'The Matrix Online'


def test_movie_combined_title_tv_series_should_have_quotes(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['title'] == '"Doctor Who"'


def test_movie_combined_title_tv_mini_series_should_have_quotes(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['band_of_brothers'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['title'] == '"Band of Brothers"'


def test_movie_combined_title_tv_episode_should_be_series_title(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who_blink'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['title'] == '"Doctor Who"'


def test_movie_combined_episode_title_should_not_include_series_title(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who_blink'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['title.episode'] == 'Blink'


def test_movie_combined_episode_title_tv_series_should_have_none(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'title.episode' not in data


def test_movie_combined_year_should_be_a_four_digit_number(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['year'] == '1999'


def test_movie_combined_year_tv_series_should_be_beginning_year(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['year'] == '2005'


def test_movie_combined_year_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['aslan'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'year' not in data


def test_movie_combined_tv_extra_tv_series_should_have_type_and_end_year(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['house_md'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['tv_extra'] == 'TV series 2004-2012'


def test_movie_combined_tv_extra_tv_mini_series_should_have_type_and_end_year(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['band_of_brothers'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['tv_extra'] == 'TV mini-series 2001-2001'


def test_movie_combined_tv_extra_continuing_tv_series_should_have_no_end_year(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['tv_extra'] == 'TV series 2005-'


def test_movie_combined_tv_extra_tv_episode_should_have_none(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who_blink'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'tv_extra' not in data


def test_movie_combined_episode_prev_link_should_be_a_title_link(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who_blink'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['episode.prev.link'] == '/title/tt1000256/'


def test_movie_combined_episode_prev_link_first_episode_should_have_none(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['house_md_first'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'episode.prev.link' not in data


def test_movie_combined_episode_number_should_be_a_number(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who_blink'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['episode.number'] == '« | 38 of | »'


def test_movie_combined_episode_series_episode_count_should_be_a_number(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['house_md_first'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['series.episode_count'] == '176 Episodes'


def test_movie_combined_episode_next_link_should_be_a_title_link(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who_blink'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['episode.next.link'] == '/title/tt1000259/'


def test_movie_combined_episode_next_link_last_episode_should_have_none(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['house_md_last'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'episode.next.link' not in data


def test_movie_combined_rating_should_be_a_decimal_number_over_10(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert re.match(r'^[1-9]\.\d\/10$', data['rating'])


def test_movie_combined_rating_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'rating' not in data


def test_movie_combined_votes_should_be_a_thousands_separated_number(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert re.match(r'^[1-9][0-9,]* votes$', data['votes'])


def test_movie_combined_votes_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'votes' not in data


def test_movie_combined_rank_top250_should_include_position_number(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert re.match(r'^Top 250: #\d+$', data['rank'])


def test_movie_combined_rank_bottom100_should_include_position_number(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['manos'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert re.match(r'^Bottom 100: #\d+$', data['rank'])


def test_movie_combined_rank_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'rank' not in data


def test_movie_combined_creators_single_should_be_a_list_of_persons(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['creators'] == [
        {'link': '/name/nm0628285/', 'name': 'Sydney Newman'}
    ]


def test_movie_combined_creators_multiple_should_be_a_list_of_persons(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['star_trek_ds9'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['creators'] == [
        {'link': '/name/nm0075834/', 'name': 'Rick Berman'},
        {'link': '/name/nm0683522/', 'name': 'Michael Piller'}
    ]


def test_movie_combined_creators_episodes_should_have_none(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who_blink'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'creators' not in data


def test_movie_combined_seasons_should_be_a_list_of_seasons(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['house_md'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['seasons'] == [str(i) for i in range(1, 9)]


def test_movie_combined_seasons_mini_series_should_have_only_one(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['band_of_brothers'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['seasons'] == ['1']


def test_movie_combined_seasons_episodes_should_have_none(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who_blink'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'seasons' not in data


def test_movie_combined_series_should_be_a_series(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who_blink'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['series'] == {'link': '/title/tt0436992/',
                              'title.full': '"Doctor Who" (2005)'}


def test_movie_combined_series_tv_series_should_have_none(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'series' not in data


def test_movie_combined_episode_air_date_should_include_season_and_episode(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who_blink'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['date.airing'] == '9 June 2007 (Season 3, Episode 10)'


def test_movie_combined_episode_air_date_tv_series_should_have_none(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'date.airing' not in data


def test_movie_combined_genres_single_should_be_a_list_of_genre_names(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['if'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['genres'] == ['Drama']


def test_movie_combined_genres_multiple_should_be_a_list_of_genre_names(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['genres'] == ['Action', 'Sci-Fi']


# TODO: find a movie with no genre
# def test_movie_combined_genres_none_should_be_excluded(imdb, movies):
#     url = TITLE_COMBINED_URL.format(imdb_id=movies['???'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
#     assert 'genres' not in data


def test_movie_combined_tagline_should_be_a_short_phrase(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['tagline'] == 'Free your mind'


def test_movie_combined_tagline_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'tagline' not in data


def test_movie_combined_plot_should_be_a_longer_text(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert re.match('^A computer hacker .* against its controllers.$', data['plot'])


def test_movie_combined_plot_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'plot' not in data


# TODO: find a movie with only one plot keyword
# def test_movie_combined_plot_keywords_single_should_be_a_list_of_keywords(imdb, movies):
#     url = TITLE_COMBINED_URL.format(imdb_id=movies['???'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
#     assert data['plot.keywords'] == ['???']


def test_movie_combined_plot_keywords_multiple_should_be_a_list_of_keywords(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['plot.keywords'] == ['Computer', 'Hacker', 'Reality',
                                     'Matrix', 'Computer Hacker']


def test_movie_combined_plot_keywords_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'plot.keywords' not in data


def test_movie_combined_cast_single_should_be_a_list_of_persons_and_characters(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix_tv'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['cast'] == [
        {'link': '/name/nm0186469/', 'name': 'Kenneth Cranham',
         'character': {'notes': 'Narrator'}}
    ]


def test_movie_combined_cast_multiple_should_be_a_list_of_persons_and_characters(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert len(data['cast']) == 38
    assert data['cast'][:2] == [
        {'link': '/name/nm0000206/', 'name': 'Keanu Reeves',
         'character': {'link': '/character/ch0000741/', 'name': 'Neo'}},
        {'link': '/name/nm0000401/', 'name': 'Laurence Fishburne',
         'character': {'link': '/character/ch0000746/', 'name': 'Morpheus'}}
    ]


def test_movie_combined_cast_character_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['cast'][0] == {'link': '/name/nm0022342/', 'name': 'Zeki Alpan'}


def test_movie_combined_cast_character_link_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['cast'][1] == {'link': '/name/nm0351657/', 'name': 'Nejat Gürçen',
                               'character': {'notes': 'Naci'}}


def test_movie_combined_cast_character_notes_should_be_included(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['cast'][14] == {'link': '/name/nm0336802/', 'name': 'Marc Aden Gray',
                                'character': {'link': '/character/ch0030779/', 'name': 'Choi',
                                              'notes': '(as Marc Gray)'}}


def test_movie_combined_cast_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix_short'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'cast' not in data


def test_movie_combined_directors_single_should_be_a_list_of_persons(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['shining'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['directors'] == [
        {'link': '/name/nm0000040/', 'name': 'Stanley Kubrick'}
    ]


def test_movie_combined_directors_multiple_should_be_a_list_of_persons(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['west_side_story'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['directors'] == [
        {'link': '/name/nm0730385/', 'name': 'Jerome Robbins'},
        {'link': '/name/nm0936404/', 'name': 'Robert Wise'}
    ]


def test_movie_combined_directors_with_notes_should_include_notes(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['directors'] == [
        {'link': '/name/nm0905154/', 'name': 'Lana Wachowski',
         'notes': '(as The Wachowski Brothers)'},
        {'link': '/name/nm0905152/', 'name': 'Lilly Wachowski',
         'notes': '(as The Wachowski Brothers)'}
    ]


def test_movie_combined_directors_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['aslan'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'directors' not in data


def test_movie_combined_writers_single_should_be_a_list_of_persons(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['writers'] == [
        {'link': '/name/nm0277168/', 'name': 'Recep Filiz'}
    ]


def test_movie_combined_writers_notes_should_be_included(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['manos'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['writers'] == [
        {'link': '/name/nm0912849/', 'name': 'Harold P. Warren',
         'notes': '(screenplay)'}
    ]


def test_movie_combined_writers_multiple_should_be_a_list_of_persons(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['shining'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['writers'] == [
        {'link': '/name/nm0000175/', 'name': 'Stephen King',
         'notes': '(novel)'},
        {'link': '/name/nm0000040/', 'name': 'Stanley Kubrick',
         'notes': '(screenplay) &'},
        {'link': '/name/nm0424956/', 'name': 'Diane Johnson',
         'notes': '(screenplay)'}
    ]


def test_movie_combined_writers_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix_tv'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'writers' not in data


def test_movie_combined_producers_single_should_be_a_list_of_persons(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['manos'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['producers'] == [
        {'link': '/name/nm0912849/', 'name': 'Harold P. Warren',
         'notes': 'producer'}
    ]


def test_movie_combined_producers_multiple_should_be_a_list_of_persons(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['producers'][-2:] == [
        {'link': '/name/nm0905154/', 'name': 'Lana Wachowski',
         'notes': 'executive producer (as Larry Wachowski)'},
        {'link': '/name/nm0905152/', 'name': 'Lilly Wachowski',
         'notes': 'executive producer (as Andy Wachowski)'}
    ]


def test_movie_combined_producers_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix_tv_short'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'producers' not in data


def test_movie_combined_aka_should_be_br_separated_titles(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['manos'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['title.aka'] == \
        '"Манос: Руки судьбы" - Soviet Union (Russian title):BR:' \
        ' "Manos - As Mãos do Destino" - Brazil (imdb display title):BR:'


def test_movie_combined_aka_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'title.aka' not in data


def test_movie_combined_mpaa_should_be_a_rating(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['rating.mpaa'] == 'Rated R for sci-fi violence and brief language'


def test_movie_combined_mpaa_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'mpaa' not in data


def test_movie_combined_runtime_single_should_be_a_number_in_minutes(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['runtime'] == '136 min'


def test_movie_combined_runtime_multiple_should_be_pipe_separated(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['shining'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['runtime'] == \
        '144 min (cut) | 119 min (cut) (European version) | 146 min (original version)'


def test_movie_combined_runtime_with_countries_should_include_context(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['suspiria'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['runtime'] == '98 min | Germany:88 min | USA:92 min | Argentina:95 min'


def test_movie_combined_runtime_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix_vg'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'runtime' not in data


def test_movie_combined_countries_single_should_be_a_list_of_countries(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['countries'] == [
        {'link': '/country/us', 'name': 'USA'}
    ]


def test_movie_combined_countries_multiple_should_be_a_list_of_countries(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['shining'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['countries'] == [
        {'link': '/country/us', 'name': 'USA'},
        {'link': '/country/gb', 'name': 'UK'}
    ]


# TODO: find a movie with no country
# def test_movie_combined_countries_none_should_be_excluded(imdb, movies):
#     url = TITLE_COMBINED_URL.format(imdb_id=movies['???'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
#     assert 'countries' not in data


def test_movie_combined_languages_single_should_be_a_list_of_languages(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['languages'] == [
        {'link': '/language/en', 'name': 'English'}
    ]


def test_movie_combined_languages_multiple_should_be_a_list_of_languages(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ace_in_the_hole'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['languages'] == [
        {'link': '/language/en', 'name': 'English'},
        {'link': '/language/es', 'name': 'Spanish'},
        {'link': '/language/la', 'name': 'Latin'}
    ]


def test_movie_combined_languages_single_none_is_a_language_name(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix_short'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['languages'] == [
        {'link': '/language/zxx', 'name': 'None'}
    ]


# TODO: find a movie with no language
# def test_movie_combined_languages_none_should_be_excluded(imdb, movies):
#     url = TITLE_COMBINED_URL.format(imdb_id=movies['???'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
#     assert 'languages' not in data


def test_movie_combined_colors_single_should_be_a_list_of_color_types(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['manos'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['colors'] == ['Color']


def test_movie_combined_colors_multiple_should_be_a_list_of_color_types(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['if'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['colors'] == ['Black and White', 'Color']


def test_movie_combined_colors_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix_tv'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'colors' not in data


def test_movie_combined_colors_notes_single_should_include_note(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['manos'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['colors.notes'] == 'Color (Eastmancolor)'


def test_movie_combined_colors_notes_multiple_should_be_pipe_separated(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['if'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['colors.notes'] == 'Black and White | Color (Eastmancolor) (uncredited)'


def test_movie_combined_colors_notes_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix_tv'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'colors.notes' not in data


def test_movie_combined_aspect_ratio_should_be_a_number_to_one(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['aspect_ratio'] == '2.35 : 1'


def test_movie_combined_aspect_ratio_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'aspect_ratio' not in data


def test_movie_combined_sound_mix_single_should_be_a_list_of_sound_mix_types(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ace_in_the_hole'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['sound_mix'] == ['Mono']


def test_movie_combined_sound_mix_multiple_should_be_a_list_of_sound_mix_types(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['sound_mix'] == ['DTS', 'Dolby Digital', 'SDDS']


def test_movie_combined_sound_mix_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'sound_mix' not in data


def test_movie_combined_sound_mix_notes_single_should_include_note(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ace_in_the_hole'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['sound_mix.notes'] == 'Mono (Western Electric Recording)'


def test_movie_combined_sound_mix_notes_multiple_should_be_pipe_separated(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['sound_mix.notes'] == 'DTS | Dolby Digital | SDDS'


def test_movie_combined_sound_mix_notes_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'sound_mix.notes' not in data


def test_movie_combined_certifications_single_should_be_a_list_of_certificates(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who_blink'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['certifications'] == ['UK:PG']


def test_movie_combined_certifications_multiple_should_be_a_list_of_certificates(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['manos'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['certifications'] == ['Canada:G', 'Finland:K-18', 'USA:Not Rated']


def test_movie_combined_certifications_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'certifications' not in data


def test_movie_combined_certifications_notes_single_include_note(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['dr_who_blink'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['certifications.notes'] == 'UK:PG (DVD rating)'


def test_movie_combined_certifications_notes_multiple_should_be_pipe_separated(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['manos'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert data['certifications.notes'] == \
        'Canada:G (Quebec) (2008) | Finland:K-18 (2008) (self applied) | USA:Not Rated'


def test_movie_combined_certifications_notes_none_should_be_excluded(imdb, movies):
    url = TITLE_COMBINED_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_COMBINED, content_format='html')
    assert 'certifications.notes' not in data


########################################
# movie taglines page tests
########################################


MOVIE_TAGLINES = 'movie_taglines'


def test_movie_taglines_single_should_be_a_list_of_phrases(imdb, movies):
    url = TITLE_TAGLINES_URL.format(imdb_id=movies['if'])
    data = scrape(url, imdb, MOVIE_TAGLINES, content_format='html')
    assert data['taglines'] == ['Which side will you be on?']


def test_movie_taglines_multiple_should_be_a_list_of_phrases(imdb, movies):
    url = TITLE_TAGLINES_URL.format(imdb_id=movies['manos'])
    data = scrape(url, imdb, MOVIE_TAGLINES, content_format='html')
    assert len(data['taglines']) == 3
    assert data['taglines'][0] == "It's Shocking! It's Beyond Your Imagination!"


def test_movie_taglines_none_should_be_excluded(imdb, movies):
    url = TITLE_TAGLINES_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_TAGLINES, content_format='html')
    assert 'taglines' not in data


########################################
# movie plot page tests
########################################


MOVIE_PLOT_SUMMARY = 'movie_plot_summary'


def test_movie_plot_summaries_should_be_a_list_of_texts(imdb, movies):
    url = TITLE_PLOT_SUMMARY_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_PLOT_SUMMARY, content_format='html')
    summaries = data['plot_summaries']
    assert summaries[0]['summary'].startswith('Thomas A. Anderson is a man ')
    assert summaries[0]['author'] == 'redcommander27'


def test_movie_plot_summaries_none_should_be_excluded(imdb, movies):
    url = TITLE_PLOT_SUMMARY_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_PLOT_SUMMARY, content_format='html')
    assert 'plot_summaries' not in data


########################################
# movie keywords page tests
########################################


MOVIE_KEYWORDS = 'movie_keywords'


def test_movie_keywords_should_be_a_list_of_keywords(imdb, movies):
    url = TITLE_KEYWORDS_URL.format(imdb_id=movies['matrix'])
    data = scrape(url, imdb, MOVIE_KEYWORDS, content_format='html')
    for keyword in ('computer', 'messiah', 'artificial reality'):
        assert keyword in data['keywords']


def test_movie_keywords_none_should_be_excluded(imdb, movies):
    url = TITLE_KEYWORDS_URL.format(imdb_id=movies['ates_parcasi'])
    data = scrape(url, imdb, MOVIE_KEYWORDS, content_format='html')
    assert 'keywords' not in data
