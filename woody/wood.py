# Copyright (C) 2014-2016 H. Turgut Uyar <uyar@tekir.org>
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
This is the module that cantains the XML scrapers.
"""

from collections import namedtuple
from hashlib import md5
from xml.etree import ElementTree

import logging
import os

from .web import html_to_xhtml, retrieve


_logger = logging.getLogger(__name__)


def xpath(element, path):
    """Apply an XPath expression to an element.

    This function is mainly needed to compensate for the lack of ``/text()``
    and ``/@attr`` queries in ElementTree XPath support.

    :param element: Element to apply the expression to.
    :param path: XPath expression to apply.
    :return: Elements or strings resulting from the query.
    """
    if path.endswith('//text()'):
        _logger.debug('handling descendant text path: %s', path)
        result = [t for e in element.findall(path[:-8])
                  for t in e.itertext() if t]
    elif path.endswith('/text()'):
        _logger.debug('handling child text path: %s', path)
        result = [t for e in element.findall(path[:-7])
                  for t in ([e.text] + [c.tail if c.tail else '' for c in e])
                  if t]
    else:
        *epath, last_step = path.split('/')
        if last_step.startswith('@'):
            _logger.debug('handling attribute path: %s', path)
            result = [e.attrib.get(last_step[1:])
                      for e in element.findall('/'.join(epath))]
            result = [r for r in result if r is not None]
        else:
            result = element.findall(path)
    return result


_REDUCERS = {
    'first': lambda xs: xs[0],
    'join': lambda xs, d='': d.join(xs)
}


Rule = namedtuple('Rule', ['key', 'path', 'reducer'])
"""A rule for extracting data from an element."""


def peck(element, rule):
    """Extract one data item from an element.

    :param element: Element to extract the data from.
    :param rule: Rule that specifies how to extract the data from the element.
    :return: Extracted data value.
    """
    values = xpath(element, rule.path)
    if len(values) == 0:
        _logger.debug('no match for %s using %s', rule.key, rule.path)
        return None

    _logger.debug('extracted data for %s: %s', rule.key, values)
    try:
        reducer = _REDUCERS[rule.reducer]
    except KeyError:
        raise ValueError('Unknown reducer: %s', rule.reducer)
    value = reducer(values)
    _logger.debug('applied %s reducer, new value %s', rule.reducer, value)
    return value


def scrape(content, rules, prune=None):
    """Extract data from an XML document.

    :param content: Content to extract the data from.
    :param rules: Rules that specify how to extract the data from the document.
    :param prune: Path for the element to act as the root of tree.
    :return: Extracted data.
    """
    root = ElementTree.fromstring(content)
    if prune is not None:
        _logger.debug('selecting new root using %s', prune)
        elements = xpath(root, prune)
        if len(elements) != 1:
            raise ValueError('Pruning expression must select exactly'
                             ' one element: {}.'.format(prune))
        root = elements[0]

    data = {}
    for rule in rules:
        value = peck(root, rule)
        if value is not None:
            data[rule.key] = value
    return data


def scrape_url(spec, scraper_id, **kwargs):
    """Extract data retrieved from a URL.

    :param spec: Data extraction specification.
    :param scraper_id: Selected scraper from the spec.
    :return: Extracted data from selected scraper.
    """
    scrapers = [s for s in spec if s['id'] == scraper_id]
    if len(scrapers) != 1:
        raise ValueError('Spec must contain exactly one id'
                         ' for a scraper: {}.'.format(scraper_id))
    scraper = scrapers[0]

    url = scraper['url'].format(**kwargs)
    cache_dir = os.environ.get('WOODY_WEB_CACHE_DIR')
    if cache_dir is None:
        content = retrieve(url)
    else:
        os.makedirs(cache_dir, exist_ok=True)
        key = md5(url.encode('utf-8')).hexdigest()
        cache_file = os.path.join(cache_dir, key)
        if not os.path.exists(cache_file):
            content = retrieve(url)
            with open(cache_file, 'w') as f:
                f.write(content)
        else:
            with open(cache_file) as f:
                content = f.read()

    content_format = scraper.get('format', 'xml')
    if content_format == 'html':
        content = html_to_xhtml(content)

    rules = [Rule(**r) for r in scraper['rules']]
    data = scrape(content, rules, prune=scraper.get('prune'))
    return data
