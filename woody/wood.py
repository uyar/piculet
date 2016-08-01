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
This module contains the components for handling XML trees.
"""

from xml.etree import ElementTree

import logging
import re


_logger = logging.getLogger(__name__)


def xpath(element, path):
    """Apply an XPath expression to an element.

    This function is mainly needed to compensate for the lack of ``text()``
    and ``@attr`` axis queries in ElementTree XPath support.

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


class WoodPecker:
    """A data extractor.

    The XPath expression is applied to an element. The expression is expected
    to generate a list of strings; therefore it has to end with ``text()``
    or ``@attr``. The resulting list will be reduced to a single value using
    the reducer function. These functions have to take a list of strings
    as parameter and return a single string as result.

    :param path: XPath expression to select the data contents.
    :param reducer: Function to reduce the data contents to a single value.
    """

    REDUCERS = {
        'first': lambda xs: xs[0],
        'join': lambda xs: ''.join(xs),
        'clean': lambda xs: re.sub('\s+', ' ', ''.join(xs)).strip(),
        'normalize': lambda xs: re.sub('[^a-z0-9]', '', ''.join(xs).lower())
    }
    """Pre-defined reducers."""

    def __init__(self, path, reducer):
        self.path = path
        try:
            self.reducer = WoodPecker.REDUCERS[reducer]
        except KeyError:
            raise ValueError('Unknown reducer: %s', reducer)

    def peck(self, element):
        """Extract a data item from an element.

        :param element: Element to extract the data from.
        :return: Extracted data value.
        """
        values = xpath(element, self.path)
        if len(values) == 0:
            _logger.debug('no match for %s', self.path)
            return None

        _logger.debug('extracted data: %s', values)
        value = self.reducer(values)
        _logger.debug('applied %s reducer, new value %s', self.reducer, value)
        return value


def extract(content, rules, prune=None):
    """Extract data from an XML document.

    :param content: Content to extract the data from.
    :param rules: Rules that specify how to extract the data.
    :param prune: Path for the element to set as root before extractions.
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
        pecker = WoodPecker(path=rule['path'], reducer=rule['reducer'])
        sections = rule.get('foreach')
        if sections is None:
            value = pecker.peck(root)
            if value is not None:
                data[rule['key']] = value
        else:
            for section in xpath(root, sections):
                key_pecker = WoodPecker(path=rule['key'],
                                        reducer=rule['key_reducer'])
                key = key_pecker.peck(section)
                pecker = WoodPecker(path=rule['path'], reducer=rule['reducer'])
                value = pecker.peck(section)
                if value is not None:
                    data[key] = value
    return data
