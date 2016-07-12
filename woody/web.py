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
This module contains the classes and functions for retrieving and processing
web pages.
"""

from collections import deque
from contextlib import redirect_stdout
from html.parser import HTMLParser
from io import StringIO
from urllib.request import build_opener, Request

import logging
import re


_logger = logging.getLogger(__name__)


# TODO: this is too fragile
_CHARSET_TAGS = {
    'meta charset':
        b'<meta charset="',
    'meta http-equiv':
        b'<meta http-equiv="content-type" content="text/html; charset='
}


def retrieve(url, charset=None, fallback_charset='utf-8'):
    """Get the contents of a web page.

    If no character set is given, this will try to figure it out
    from the corresponding ``meta`` tags.

    :param url: Address of web page to retrieve.
    :param charset: Character set of the page.
    :param fallback_charset: Character set to use if it can't be figured out.
    :return: Content of web page.
    """
    _logger.debug('retrieving page: %s', url)
    opener = build_opener()
    request = Request(url)
    with opener.open(request) as response:
        content = response.read()
    _logger.debug('read %s bytes', len(content))

    if charset is None:
        for key, tag in _CHARSET_TAGS.items():
            start = content.find(tag)
            if start >= 0:
                _logger.debug('charset found in %s tag', key)
                meta_tag, meta_start = tag, start
                break
        else:
            meta_tag, meta_start = None, -1

        if meta_tag is not None:
            charset_start = meta_start + len(meta_tag)
            charset_end = content.find(b'"', charset_start)
            charset = content[charset_start:charset_end].decode('ascii')
        else:
            _logger.debug('charset not found, using fallback')
            charset = fallback_charset

    _logger.debug('decoding for charset: %s', charset)
    return content.decode(charset)


class _HTMLNormalizer(HTMLParser):
    """HTML cleaner and XHTML converter.

    DOCTYPE declarations and comments are removed.

    :param omit_tags: Tags to remove, along with all their content.
    :param omit_attrs: Attributes to remove.
    """

    SELF_CLOSING_TAGS = {'br', 'hr', 'img', 'input', 'link', 'meta'}
    """Tags to handle as self-closing."""

    ENTITY_REFS = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;'
    }
    """Entity references to replace."""

    ATTR_ENTITY_REFS = {
        '"': '&quot;'
    }
    """Additional entity references to replace in attributes."""

    # FIXME: what if it's the last attribute?
    _RE_QUOTE_FIXER = re.compile(r'\s\w+="(".*?)"\s+\w+=')

    def __init__(self, omit_tags=None, omit_attrs=None):
        # let the HTML parser convert entity refs to unicode chars
        super().__init__(convert_charrefs=True)

        self.omit_tags = omit_tags if omit_tags is not None else set()
        self.omit_attrs = omit_attrs if omit_attrs is not None else set()

        # stacks used during normalization
        self._open_tags = deque()
        self._open_omitted_tags = deque()

    def handle_starttag(self, tag, attrs):
        if tag in self.omit_tags:
            _logger.debug('omitting tag: %s', tag)
            self._open_omitted_tags.append(tag)
        if not self._open_omitted_tags:
            # stack empty -> not in omit mode
            if (tag == 'li') and (self._open_tags[-1] == 'li'):
                _logger.debug('opened li without closing previous li, adding closing tag')
                self.handle_endtag('li')
            attribs = []
            for attr_name, attr_value in attrs:
                if attr_name in self.omit_attrs:
                    _logger.debug('omitting attribute: %s', attr_name)
                else:
                    if not attr_value:
                        _logger.debug('no value for %s attribute, adding empty value',
                                      attr_name)
                        attr_value = ''
                    else:
                        for e, r in self.ENTITY_REFS.items():
                            attr_value = attr_value.replace(e, r)
                        for e, r in self.ATTR_ENTITY_REFS.items():
                            attr_value = attr_value.replace(e, r)
                    attribs.append((attr_name, attr_value))
            line = '<{tag}{attrs}{slash}>'.format(
                tag=tag,
                attrs=''.join([' {name}="{value}"'.format(name=n, value=v)
                               for n, v in attribs]),
                slash=' /' if tag in self.SELF_CLOSING_TAGS else ''
            )
            print(line, end='')
            if tag not in self.SELF_CLOSING_TAGS:
                self._open_tags.append(tag)

    def handle_endtag(self, tag):
        if not self._open_omitted_tags:
            # stack empty -> not in omit mode
            if tag not in self.SELF_CLOSING_TAGS:
                last = self._open_tags[-1]
                if (tag == 'ul') and (last == 'li'):
                    _logger.debug('closing ul without closing last li, adding closing tag')
                    self.handle_endtag('li')
                if tag == last:
                    # expected end tag
                    print('</{t}>'.format(t=tag), end='')
                    self._open_tags.pop()
                elif tag not in self._open_tags:
                    _logger.debug('end tag without a start tag: %s', tag)
                    # XXX: for <a><b></a></b>, this case gets invoked
                    #      after the case below
                elif tag == self._open_tags[-2]:
                    _logger.debug('unexpected end tag: %s instead of %s, closing both',
                                  tag, last)
                    print('</{t}>'.format(t=last), end='')
                    print('</{t}>'.format(t=tag), end='')
                    self._open_tags.pop()
                    self._open_tags.pop()
        elif (tag in self.omit_tags) and (tag == self._open_omitted_tags[-1]):
            # end of expected omitted tag
            self._open_omitted_tags.pop()

    def handle_data(self, data):
        if not self._open_omitted_tags:
            # stack empty -> not in omit mode
            for e, r in self.ENTITY_REFS.items():
                data = data.replace(e, r)
            print(data, end='')

    def feed(self, data):
        # fix for quotes in attribute values
        for problem in self._RE_QUOTE_FIXER.findall(data):
            data = data.replace(problem, problem.replace('"', '&quot;'))
        super().feed(data)
        # close all remaining open tags
        # for tag in reversed(self._open_tags):
        #     print('</{t}>'.format(t=tag), end='')


def html_to_xhtml(content, omit_tags=None, omit_attrs=None):
    """Clean HTML and convert to XHTML.

    :param content: HTML content to clean and convert.
    :param omit_tags: Tags to exclude from the output.
    :param omit_attrs: Attributes to exclude from the output.
    :return: Normalized XHTML content.
    """
    _logger.debug('cleaning HTML and converting to XHTML')
    out = StringIO()
    normalizer = _HTMLNormalizer(omit_tags=omit_tags, omit_attrs=omit_attrs)
    with redirect_stdout(out):
        normalizer.feed(content)
    return out.getvalue()
