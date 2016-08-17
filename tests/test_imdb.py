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
        'suspiria': 76786               # multiple country runtimes
    }


@fixture(scope='module', autouse=True)
def get_imdb_pages(imdb, movies):
    """Store all needed pages from the IMDb in the cache."""
    for scraper in imdb['scrapers']:
        for movie_id in movies.values():
            url = imdb['base_url'] + scraper['url'].format(imdb_id=movie_id)
            _get_document(url)


def test_full_title_should_have_title_and_year(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['title.full'] == 'The Matrix (1999)'


def test_full_title_video_movie_should_include_type(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_video'])
    assert data['title.full'] == 'Armitage III: Poly Matrix (1996) (V)'


def test_full_title_tv_movie_should_include_type(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_tv'])
    assert data['title.full'] == 'The Matrix Defence (2003) (TV)'


def test_full_title_video_game_should_include_type(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_vg'])
    assert data['title.full'] == 'The Matrix Online (2005) (VG)'


def test_full_title_tv_series_should_have_quotes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who'])
    assert data['title.full'] == '"Doctor Who" (2005)'


def test_full_title_tv_mini_series_should_have_quotes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['band_of_brothers'])
    assert data['title.full'] == '"Band of Brothers" (2001)'


def test_full_title_tv_episode_should_include_series_title_in_quotes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who_blink'])
    assert data['title.full'] == '"Doctor Who" Blink (2007)'


def test_poster_should_have_link(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['poster.link'].endswith('._V1._SX94_SY140_.jpg')


def test_poster_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'poster.link' not in data


def test_title_should_not_have_year(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['title'] == 'The Matrix'


def test_title_video_movie_should_not_include_type(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_video'])
    assert data['title'] == 'Armitage III: Poly Matrix'


def test_title_tv_movie_should_not_include_type(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_tv'])
    assert data['title'] == 'The Matrix Defence'


def test_title_video_game_should_not_include_type(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_vg'])
    assert data['title'] == 'The Matrix Online'


def test_title_tv_series_should_have_quotes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who'])
    assert data['title'] == '"Doctor Who"'


def test_title_tv_mini_series_should_have_quotes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['band_of_brothers'])
    assert data['title'] == '"Band of Brothers"'


def test_title_tv_episode_should_be_series_title_in_quotes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who_blink'])
    assert data['title'] == '"Doctor Who"'


def test_episode_title_should_not_include_series_title(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who_blink'])
    assert data['title.episode'] == 'Blink'


def test_episode_title_tv_series_should_have_none(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who'])
    assert 'title.episode' not in data


def test_year_should_be_a_four_digit_number(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['year'] == '1999'


def test_year_tv_series_should_be_a_four_digit_number(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who'])
    assert data['year'] == '2005'


def test_year_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['aslan'])
    assert 'year' not in data


def test_tv_extra_tv_series_ended_should_have_type_and_end_year(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['house_md'])
    assert data['tv_extra'] == 'TV series 2004-2012'


def test_tv_extra_tv_mini_series_ended_should_have_type_and_end_year(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['band_of_brothers'])
    assert data['tv_extra'] == 'TV mini-series 2001-2001'


def test_tv_extra_tv_series_continuing_should_have_no_end_year(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who'])
    assert data['tv_extra'] == 'TV series 2005-'


def test_tv_extra_tv_episode_should_have_none(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who_blink'])
    assert 'tv_extra' not in data


def test_episode_prev_link_should_be_a_title_link(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who_blink'])
    assert data['episode.prev.link'] == '/title/tt1000256/'


def test_episode_prev_link_first_episode_should_have_none(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['house_md_first'])
    assert 'episode.prev.link' not in data


def test_episode_number_should_be_a_number(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who_blink'])
    assert data['episode.number'] == '« | 38 of | »'


def test_episode_series_episode_count_should_be_a_number(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['house_md_first'])
    assert data['series.episode_count'] == '176 Episodes'


def test_episode_next_link_should_be_a_title_link(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who_blink'])
    assert data['episode.next.link'] == '/title/tt1000259/'


def test_episode_next_link_last_episode_should_have_none(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['house_md_last'])
    assert 'episode.next.link' not in data


def test_rating_should_be_a_decimal_number_over_10(imdb, movies):
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


def test_directors_single_should_be_a_list_of_person_links_and_names(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['shining'])
    assert data['directors'] == [
        {'link': '/name/nm0000040/', 'name': 'Stanley Kubrick'}
    ]


def test_directors_multiple_should_be_a_list_of_person_links_and_names(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['directors'] == [
        {'link': '/name/nm0905154/', 'name': 'Lana Wachowski'},
        {'link': '/name/nm0905152/', 'name': 'Lilly Wachowski'}
    ]


def test_directors_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['aslan'])
    assert 'directors' not in data


# TODO: find a movie with director notes
# def test_directors_none_should_be_excluded(imdb, movies):
#     data = scrape(imdb, 'movie_combined_details', imdb_id=movies['???'])
#     assert 'directors.notes' == '???'


def test_writers_single_should_be_a_list_of_person_links_and_names(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['manos'])
    assert data['writers'] == [
        {'link': '/name/nm0912849/', 'name': 'Harold P. Warren'}
    ]


def test_writers_multiple_should_be_a_list_of_person_links_and_names(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['shining'])
    assert data['writers'] == [
        {'link': '/name/nm0000175/', 'name': 'Stephen King'},
        {'link': '/name/nm0000040/', 'name': 'Stanley Kubrick'}
    ]


def test_writers_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_tv'])
    assert 'writers' not in data


def test_writers_notes_single_should_include_writer_notes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['manos'])
    assert data['writers.notes'] == 'Harold P. Warren (screenplay):BR:'


def test_writers_notes_multiple_should_include_writer_notes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['shining'])
    assert data['writers.notes'] == \
        'Stephen King (novel):BR: Stanley Kubrick (screenplay) ...:BR:'


def test_writers_notes_none_should_be_just_person_names(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert data['writers.notes'] == 'Recep Filiz :BR:'


def test_writers_notes_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_tv'])
    assert 'writers.notes' not in data


def test_creators_single_should_be_a_list_of_person_links_and_names(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who'])
    assert data['creators'] == [
        {'link': '/name/nm0628285/', 'name': 'Sydney Newman'}
    ]


def test_creators_multiple_should_be_a_list_of_person_links_and_names(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['star_trek_ds9'])
    assert data['creators'] == [
        {'link': '/name/nm0075834/', 'name': 'Rick Berman'},
        {'link': '/name/nm0683522/', 'name': 'Michael Piller'}
    ]


def test_creators_episodes_should_have_none(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who_blink'])
    assert 'creators' not in data


def test_seasons_should_be_a_list_of_season_links_and_names(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['house_md'])
    assert data['seasons'] == [
        {'link': 'episodes?season={}'.format(i), 'name': str(i)}
        for i in range(1, 9)
    ]


def test_seasons_mini_series_should_have_only_one(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['band_of_brothers'])
    assert data['seasons'] == [
        {'link': 'episodes?season=1', 'name': '1'}
    ]


def test_seasons_episodes_should_have_none(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who_blink'])
    assert 'seasons' not in data


def test_series_should_be_a_series_link_and_name(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who_blink'])
    assert data['series'] == {'link': '/title/tt0436992/',
                              'title.full': '"Doctor Who" (2005)'}


def test_series_tv_series_should_have_none(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who'])
    assert 'series' not in data


def test_episode_original_air_date_should_include_season_and_episode(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who_blink'])
    assert data['date.airing'] == '9 June 2007 (Season 3, Episode 10)'


def test_episode_original_air_date_tv_series_should_have_none(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who'])
    assert 'date.airing' not in data


def test_genres_single_should_be_a_list_of_genre_names(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['if'])
    assert data['genres'] == ['Drama']


def test_genres_multiple_should_be_a_list_of_genre_names(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['genres'] == ['Action', 'Sci-Fi']


# TODO: find a movie with no genre
# def test_genres_none_should_be_excluded(imdb, movies):
#     data = scrape(imdb, 'movie_combined_details', imdb_id=movies['???'])
#     assert 'genres' not in data


def test_tagline_should_be_a_short_phrase(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['tagline'] == 'Free your mind'


def test_tagline_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'tagline' not in data


def test_plot_should_be_a_longer_text(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert re.match('^A computer hacker .* against its controllers.$', data['plot'])


def test_plot_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'plot' not in data


# TODO: find a movie with only one plot keyword
# def test_plot_keywords_single_should_be_a_list_of_keywords(imdb, movies):
#     data = scrape(imdb, 'movie_combined_details', imdb_id=movies['???'])
#     assert data['plot.keywords'] == ['???']


def test_plot_keywords_multiple_should_be_a_list_of_keywords(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['plot.keywords'] == \
        ['Computer', 'Hacker', 'Reality', 'Matrix', 'Computer Hacker']


def test_plot_keywords_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'plot.keywords' not in data


def test_aka_should_be_br_separated_titles(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['manos'])
    assert data['title.aka'] == \
        '"Манос: Руки судьбы" - Soviet Union (Russian title):BR:' \
        ' "Manos - As Mãos do Destino" - Brazil (imdb display title):BR:'


def test_aka_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'title.aka' not in data


def test_mpaa_should_be_a_rating(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['rating.mpaa'] == 'Rated R for sci-fi violence and brief language'


def test_mpaa_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'mpaa' not in data


def test_runtime_single_should_be_a_number_in_minutes(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['runtime'] == '136 min'


def test_runtime_multiple_should_be_pipe_separated(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['shining'])
    assert data['runtime'] == \
        '144 min (cut) | 119 min (cut) (European version) | 146 min (original version)'


def test_runtime_with_countries_should_include_context(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['suspiria'])
    assert data['runtime'] == '98 min | Germany:88 min | USA:92 min | Argentina:95 min'


def test_runtime_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_vg'])
    assert 'runtime' not in data


def test_countries_single_should_be_a_list_of_country_links_and_names(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['countries'] == [
        {'link': '/country/us', 'name': 'USA'}
    ]


def test_countries_multiple_should_be_a_list_of_country_links_and_names(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['shining'])
    assert data['countries'] == [
        {'link': '/country/us', 'name': 'USA'},
        {'link': '/country/gb', 'name': 'UK'}
    ]


# TODO: find a movie with no country
# def test_countries_none_should_be_excluded(imdb, movies):
#     data = scrape(imdb, 'movie_combined_details', imdb_id=movies['???'])
#     assert 'countries' not in data


def test_languages_single_should_be_a_list_of_language_links_and_names(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['languages'] == [
        {'link': '/language/en', 'name': 'English'}
    ]


def test_languages_multiple_should_be_a_list_of_language_links_and_names(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ace_in_the_hole'])
    assert data['languages'] == [
        {'link': '/language/en', 'name': 'English'},
        {'link': '/language/es', 'name': 'Spanish'},
        {'link': '/language/la', 'name': 'Latin'}
    ]


def test_languages_single_none_is_a_language_name(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_short'])
    assert data['languages'] == [
        {'link': '/language/zxx', 'name': 'None'}
    ]


# TODO: find a movie with no language
# def test_languages_none_should_be_excluded(imdb, movies):
#     data = scrape(imdb, 'movie_combined_details', imdb_id=movies['???'])
#     assert 'languages' not in data


def test_colors_single_should_be_a_list_of_color_types(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['manos'])
    assert data['colors'] == ['Color']


def test_colors_multiple_should_be_a_list_of_color_types(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['if'])
    assert data['colors'] == ['Black and White', 'Color']


def test_colors_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_tv'])
    assert 'colors' not in data


def test_colors_notes_single_should_include_color_note(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['manos'])
    assert data['colors.notes'] == 'Color (Eastmancolor)'


def test_colors_notes_multiple_should_be_pipe_separated(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['if'])
    assert data['colors.notes'] == 'Black and White | Color (Eastmancolor) (uncredited)'


def test_colors_notes_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_tv'])
    assert 'colors.notes' not in data


def test_aspect_ratio_should_be_a_number_to_one(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['aspect_ratio'] == '2.35 : 1'


def test_aspect_ratio_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'aspect_ratio' not in data


def test_sound_mix_single_should_be_a_sound_mix_type(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['shining'])
    assert data['sound_mix'] == 'Mono'


def test_sound_mix_with_note_should_include_note(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ace_in_the_hole'])
    assert data['sound_mix'] == 'Mono (Western Electric Recording)'


def test_sound_mix_multiple_should_be_pipe_separated(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix'])
    assert data['sound_mix'] == 'DTS | Dolby Digital | SDDS'


def test_sound_mix_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'sound_mix' not in data


def test_certification_single_should_have_context(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['matrix_vg'])
    assert data['certification'] == 'USA:T'


def test_certification_with_note_should_include_note(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['dr_who_blink'])
    assert data['certification'] == 'UK:PG (DVD rating)'


def test_certification_multiple_should_be_pipe_separated(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['manos'])
    assert data['certification'] == \
        'Canada:G (Quebec) (2008) | Finland:K-18 (2008) (self applied) | USA:Not Rated'


def test_certification_none_should_be_excluded(imdb, movies):
    data = scrape(imdb, 'movie_combined_details', imdb_id=movies['ates_parcasi'])
    assert 'certification' not in data
