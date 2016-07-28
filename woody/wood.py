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
from enum import Enum

import logging


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


class Reducer(Enum):
    first = lambda xs: xs[0]
    join = lambda xs: ''.join(xs)


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

    _logger.debug('extracted value for %s: %s', rule.key, values)
    value = rule.reducer(values)
    _logger.debug('applied %s, new value %s', rule.reducer, value)
    return value
