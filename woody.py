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
Woody is a module for extracting data out of XML/HTML documents using XPath
queries.


Command-Line Interface
----------------------

Woody includes a command line interface::

  $ woody -h
    usage: woody [-h] [--debug] command ...

    positional arguments:
      command
        h2x       convert HTML to XHTML

    optional arguments:
      -h, --help  show this help message and exit
      --debug     enable debug messages

The :command:`h2x` command converts an HTML input to XHTML. It takes the file
name as input and prints the converted content to stdout. If the input file
name is given as ``-`` it will read the content from stdin and therefore it
can be used as part of a pipe::

  $ woody h2x foo.html
  ...
  $ cat foo.html | woody h2x -
  ...
"""


from argparse import ArgumentParser
from collections import deque
from contextlib import redirect_stdout
from hashlib import md5
from html.parser import HTMLParser
from io import StringIO
from urllib.request import build_opener, Request
from xml.etree import ElementTree

import logging
import os
import re
import sys


_logger = logging.getLogger(__name__)


###########################################################
# WEB OPERATIONS
###########################################################


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


###########################################################
### DATA EXTRACTION OPERATIONS
###########################################################


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


def woodpecker(path, reducer):
    """A data extractor that combines an XPath query with a reducing function.

    The XPath expression is applied to an element. The expression is expected
    to generate a list of strings; therefore it has to end with ``text()``
    or ``@attr``. The resulting list will be reduced to a single value using
    the reducer function. These functions have to take a list of strings
    as parameter and return a single string as result.

    :param path: XPath expression to select the data contents.
    :param reducer: Function to reduce the data contents to a single value.
    :return: A callable that can apply this path and reducer to an element.
    """

    REDUCERS = {
        'first': lambda xs: xs[0],
        'join': lambda xs: ''.join(xs),
        'clean': lambda xs: re.sub('\s+', ' ', ''.join(xs)).strip(),
        'normalize': lambda xs: re.sub('[^a-z0-9]', '', ''.join(xs).lower())
    }
    """Pre-defined reducers."""

    try:
        reduce = REDUCERS[reducer]
    except KeyError:
        raise ValueError('Unknown reducer: %s', reducer)

    def apply(element):
        """Extract a data item from an element.

        :param element: Element to extract the data from.
        :return: Extracted data value.
        """
        values = xpath(element, path)
        if len(values) == 0:
            _logger.debug('no match for %s', path)
            return None

        _logger.debug('extracted data: %s', values)
        value = reduce(values)
        _logger.debug('applied %s reducer, new value %s', reducer, value)
        return value

    return apply


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
        pecker = woodpecker(path=rule['path'], reducer=rule['reducer'])
        sections = rule.get('foreach')
        if sections is None:
            value = pecker(root)
            if value is not None:
                data[rule['key']] = value
        else:
            for section in xpath(root, sections):
                key_pecker = woodpecker(path=rule['key'],
                                        reducer=rule['key_reducer'])
                key = key_pecker(section)
                pecker = woodpecker(path=rule['path'], reducer=rule['reducer'])
                value = pecker(section)
                if value is not None:
                    data[key] = value
    return data


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
        key = md5(url.encode('utf-8')).hexdigest()
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


###########################################################
### COMMAND-LINE INTERFACE
###########################################################


def _get_parser():
    """Get a parser for command line arguments."""

    def h2x(arguments):
        _logger.debug('converting HTML to XHTML')
        if arguments.file == '-':
            _logger.debug('reading from stdin')
            content = sys.stdin.read()
        else:
            filename = os.path.abspath(arguments.file)
            _logger.debug('reading from file: %s', filename)
            with open(filename) as f:
                content = f.read()
        print(html_to_xhtml(content), end='')

    parser = ArgumentParser()
    parser.add_argument('--debug', action='store_true',
                        help='enable debug messages')

    commands = parser.add_subparsers(metavar='command', dest='command')

    subparser = commands.add_parser('h2x', help='convert HTML to XHTML')
    subparser.set_defaults(func=h2x)
    subparser.add_argument('file', help='file to convert')

    return parser


def main():
    """Entry point of the command line utility."""
    parser = _get_parser()
    arguments = parser.parse_args()

    # set debug mode
    if arguments.debug:
        logging.basicConfig(level=logging.DEBUG)
        _logger.debug('running in debug mode')

    # run the handler for the selected command
    try:
        arguments.func(arguments)
    except AttributeError:
        parser.print_usage()
        sys.exit(1)


if __name__ == '__main__':
    main()
