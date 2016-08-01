# Copyright (C) 2016 H. Turgut Uyar <uyar@tekir.org>
#
# This file is part of Woody.
#
# Woody is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Woody is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Woody.  If not, see <http://www.gnu.org/licenses/>.

"""
This module contains the main components for scraping HTML/XML documents.
"""

import hashlib
import logging
import os

from .web import html_to_xhtml, retrieve
from .wood import extract


_logger = logging.getLogger(__name__)


def _get_document(url):
    """Get the document with the given URL.

    This function will check whether the requested document has already been
    retrieved and return the cached content if possible. Note that
    cached documents are assumed to be up-to-date.

    :param url: URL to get the document from.
    :return: Content of the retrieved document.
    """
    cache_dir = os.environ.get('WOODY_WEB_CACHE_DIR')
    if cache_dir is None:
        _logger.debug('no caching, retrieving document')
        content = retrieve(url)
    else:
        _logger.debug('using cache dir %s', cache_dir)
        os.makedirs(cache_dir, exist_ok=True)
        key = hashlib.md5(url.encode('utf-8')).hexdigest()
        cache_file = os.path.join(cache_dir, key)
        if not os.path.exists(cache_file):
            _logger.debug('document not in cache, retrieving and storing')
            content = retrieve(url)
            with open(cache_file, 'w') as f:
                f.write(content)
        else:
            _logger.debug('using document found in cache')
            with open(cache_file) as f:
                content = f.read()
    return content


def scrape(spec, scraper_id, **kwargs):
    """Extract data from a document according to a specification.

    All keyword arguments will be used as parameters in the format string
    of the scraper URL.

    :param spec: Data extraction specification, a JSON list.
    :param scraper_id: Selected scraper from the spec.
    :return: Extracted data.
    """
    scrapers = [s for s in spec['scrapers'] if s['id'] == scraper_id]
    if len(scrapers) != 1:
        raise ValueError('Scraper ids must be unique: %s'.format(scraper_id))
    scraper = scrapers[0]
    _logger.debug('using scraper %s', scraper)

    base_url = spec['base_url']
    url = base_url + scraper['url'].format(**kwargs)
    _logger.debug('scraping url %s', url)

    content = _get_document(url)

    content_format = scraper.get('format', 'xml')
    if content_format == 'html':
        _logger.debug('converting html document to xml')
        content = html_to_xhtml(content)

    data = extract(content, scraper['rules'], prune=scraper.get('prune'))
    return data
