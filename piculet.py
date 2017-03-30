# Copyright (C) 2014-2017 H. Turgut Uyar <uyar@tekir.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Piculet is a package for extracting data from XML documents using XPath queries.
It can also scrape web pages by first converting the HTML source into XHTML.
Piculet consists of this single source file with no dependencies other than
the standard library, which makes it very easy to integrate into applications.

For more details, please refer to the documentation: http://piculet.readthedocs.io/
"""

from argparse import ArgumentParser
from collections import deque
from contextlib import redirect_stdout
from functools import partial
from hashlib import md5
from html import escape as html_escape
from html.parser import HTMLParser
from io import StringIO
from urllib.request import urlopen

import json
import logging
import os
import re
import sys


_logger = logging.getLogger(__name__)


###########################################################
# HTML OPERATIONS
###########################################################


# TODO: this is too fragile
_CHARSET_TAGS = {
    'meta charset':
        b'<meta charset="',
    'meta http-equiv':
        b'<meta http-equiv="content-type" content="text/html; charset='
}


def decode_html(content, charset=None, fallback_charset='utf-8'):
    """Decode an HTML document according to a character set.

    If no character set is given, this will try to figure it out
    from the corresponding ``meta`` tags.

    :sig: (bytes, Optional[str], Optional[str]) -> str
    :param content: Content of HTML document to decode.
    :param charset: Character set of the page.
    :param fallback_charset: Character set to use if it can't be figured out.
    :return: Decoded content of the document.
    """
    if charset is None:
        for key, tag in _CHARSET_TAGS.items():
            start = content.find(tag)
            if start >= 0:
                _logger.debug('charset found in [%s] tag', key)
                charset_start = start + len(tag)
                charset_end = content.find(b'"', charset_start)
                charset = content[charset_start:charset_end].decode('ascii')
                break
        else:
            _logger.debug('charset not found, using fallback')
            charset = fallback_charset
    _logger.debug('decoding for charset [%s]', charset)
    return content.decode(charset)


class HTMLNormalizer(HTMLParser):
    """HTML cleaner and XHTML converter.

    DOCTYPE declarations and comments are removed.

    :sig: (Set[str], Set[str]) -> None
    :param omit_tags: Tags to remove, along with all their content.
    :param omit_attrs: Attributes to remove.
    """

    SELF_CLOSING_TAGS = {'br', 'hr', 'img', 'input', 'link', 'meta'}
    """Tags to handle as self-closing."""

    def __init__(self, omit_tags=(), omit_attrs=()):
        super().__init__(convert_charrefs=True)

        self.omit_tags = set(omit_tags)    # sig: Set[str]
        self.omit_attrs = set(omit_attrs)  # sig: Set[str]

        # stacks used during normalization
        self._open_tags = deque()
        self._open_omitted_tags = deque()

    def handle_starttag(self, tag, attrs):
        if tag in self.omit_tags:
            _logger.debug('omitting [%s] tag', tag)
            self._open_omitted_tags.append(tag)
        if not self._open_omitted_tags:
            # stack empty -> not in omit mode
            if (tag == 'li') and (self._open_tags[-1] == 'li'):
                _logger.debug('opened [li] without closing previous [li], adding closing tag')
                self.handle_endtag('li')
            attribs = []
            for attr_name, attr_value in attrs:
                if attr_name in self.omit_attrs:
                    _logger.debug('omitting [%s] attribute of [%s] tag', attr_name, tag)
                    continue
                if attr_value is None:
                    _logger.debug('no value for [%s] attribute of [%s] tag, adding empty value',
                                  attr_name, tag)
                    attr_value = ''
                attribs.append((attr_name, attr_value))
            attrs = ['%(name)s="%(value)s"' % {
                'name': name,
                'value': html_escape(value, quote=True)
            } for name, value in attribs]
            line = '<%(tag)s%(attrs)s%(slash)s>' % {
                'tag': tag,
                'attrs': (' ' + ' '.join(attrs)) if len(attrs) > 0 else '',
                'slash': ' /' if tag in self.SELF_CLOSING_TAGS else ''
            }
            print(line, end='')
            if tag not in self.SELF_CLOSING_TAGS:
                self._open_tags.append(tag)

    def handle_endtag(self, tag):
        if not self._open_omitted_tags:
            # stack empty -> not in omit mode
            if tag not in self.SELF_CLOSING_TAGS:
                last = self._open_tags[-1]
                if (tag == 'ul') and (last == 'li'):
                    _logger.debug('closing [ul] without closing last [li], adding closing tag')
                    self.handle_endtag('li')
                if tag == last:
                    # expected end tag
                    print('</%(tag)s>' % {'tag': tag}, end='')
                    self._open_tags.pop()
                elif tag not in self._open_tags:
                    _logger.debug('end tag [%s] without start tag', tag)
                    # XXX: for <a><b></a></b>, this case gets invoked after the case below
                elif tag == self._open_tags[-2]:
                    _logger.debug('unexpected end tag [%s] instead of [%s], closing both',
                                  tag, last)
                    print('</%(tag)s>' % {'tag': last}, end='')
                    print('</%(tag)s>' % {'tag': tag}, end='')
                    self._open_tags.pop()
                    self._open_tags.pop()
        elif (tag in self.omit_tags) and (tag == self._open_omitted_tags[-1]):
            # end of expected omitted tag
            self._open_omitted_tags.pop()

    def handle_data(self, data):
        if not self._open_omitted_tags:
            # stack empty -> not in omit mode
            print(html_escape(data), end='')

    # def feed(self, data):
        # super().feed(data)
        # close all remaining open tags
        # for tag in reversed(self._open_tags):
        #     print('</%(tag)s>' % {'tag': tag}, end='')


def html_to_xhtml(document, omit_tags=(), omit_attrs=()):
    """Clean HTML and convert to XHTML.

    :sig: (str, Optional[Iterable[str]], Optional[Iterable[str]]) -> str
    :param document: HTML document to clean and convert.
    :param omit_tags: Tags to exclude from the output.
    :param omit_attrs: Attributes to exclude from the output.
    :return: Normalized XHTML content.
    """
    _logger.debug('cleaning html and converting to xhtml')
    out = StringIO()
    normalizer = HTMLNormalizer(omit_tags=omit_tags, omit_attrs=omit_attrs)
    with redirect_stdout(out):
        normalizer.feed(document)
    return out.getvalue()


###########################################################
# DATA EXTRACTION OPERATIONS
###########################################################

try:
    from lxml import etree as ElementTree
    _USE_LXML = True
    _logger.debug('using lxml')
except ImportError:
    from xml.etree import ElementTree
    _USE_LXML = False
    _logger.debug('lxml not found, falling back to elementtree')


def build_tree(document):
    """Build a tree from an XML document.

    :sig: (str) -> ElementTree.Element
    :param document: XML document to build the tree from.
    :return: Root node of the XML tree.
    """
    return ElementTree.fromstring(document)


def xpath_etree(element, path):
    """Apply an XPath expression to an element.

    This function is mainly needed to compensate for the lack of ``text()``
    and ``@attr`` axis queries in ElementTree XPath support.

    :sig: (ElementTree.Element, str) -> Union[List[str], List[ElementTree.Element]]
    :param element: Element to apply the expression to.
    :param path: XPath expression to apply.
    :return: Elements or strings resulting from the query.
    """
    if path.endswith('//text()'):
        _logger.debug('handling descendant text path [%s]', path)
        return [t for e in element.findall(path[:-8]) for t in e.itertext() if t]

    if path.endswith('/text()'):
        _logger.debug('handling child text path [%s]', path)
        return [t for e in element.findall(path[:-7])
                for t in ([e.text] + [c.tail if c.tail else '' for c in e]) if t]

    *epath, last_step = path.split('/')
    if last_step.startswith('@'):
        _logger.debug('handling attribute path [%s]', path)
        result = [e.attrib.get(last_step[1:]) for e in element.findall('/'.join(epath))]
        return [r for r in result if r is not None]

    _logger.debug('handling element producing path [%s]', path)
    return element.findall(path)


xpath = ElementTree._Element.xpath if _USE_LXML else xpath_etree


_REDUCERS = {
    'first': lambda xs: xs[0],
    'join': lambda xs: ''.join(xs),
    'clean': lambda xs: re.sub('\s+', ' ', ''.join(xs)).strip(),
    'normalize': lambda xs: re.sub('[^a-z0-9_]', '',
                                   ''.join(xs).lower().replace(' ', '_'))
}
"""Pre-defined reducers."""


def woodpecker(path, reducer):
    """A value extractor that combines an XPath query with a reducing function.

    This function returns a callable that takes an XML element as parameter and
    applies the XPath query to that element to get a list of strings; therefore
    the query has to end with ``text()`` or ``@attr``. The list will then be
    passed to the reducer function to generate a single string as the result.

    :sig: (str, str) -> Callable[[ElementTree.Element], Optional[str]]
    :param path: XPath query to select the values.
    :param reducer: Name of reducer function.
    :return: A callable that can apply this path and reducer to an element.
    """
    try:
        reduce = _REDUCERS[reducer]
    except KeyError:
        raise ValueError('Unknown reducer [%s]', reducer)

    def apply(element):
        """Extract a value from an element.

        :param element: Element to extract the value from.
        :return: Extracted value.
        """
        values = xpath(element, path)
        if len(values) == 0:
            _logger.debug('no match for [%s]', path)
            return None

        _logger.debug('extracted value [%s]', values)
        value = reduce(values)
        _logger.debug('applied [%s] reducer, new value [%s]', reducer, value)
        return value

    return apply


def extract(root, items, pre=()):
    """Extract data from an XML tree.

    This will convert extract the data items according to the supplied rules.
    If given, it will use the ``pre`` parameter to carry out preprocessing
    operations on the tree before starting data extraction.

    :sig:
        (
            ElementTree.Element,
            Iterable[Mapping[str, Any]],
            Optional[Iterable[Mapping[str, Any]]]
        ) -> Mapping[str, Any]
    :param root: Root of the XML tree to extract the data from.
    :param items: Rules that specify how to extract the data items.
    :param pre: Preprocessing operations on the document tree.
    :return: Extracted data.
    """

    def gen(val):
        """Value generator function.

        It takes a value generator description and returns a callable that
        takes an XML element and returns a value.
        """
        assert isinstance(val, str) or ('path' in val) or ('items' in val)
        if isinstance(val, str):
            # constant function
            return lambda _: val
        if 'path' in val:
            # xpath and reducer
            return woodpecker(val['path'], val['reducer'])
        if 'items' in val:
            # recursive function for applying subrules
            return partial(extract, items=val['items'], pre=val.get('pre', ()))

    def parent_getter():
        if _USE_LXML:
            return ElementTree._Element.getparent
        else:
            # ElementTree doesn't support parent queries, so build a map for it
            # TODO: this re-traverses tree on subrules
            parents = {e: p for p in root.iter() for e in p}
            return parents.get

    get_parent = parent_getter()

    # do the preprocessing operations
    for step in pre:
        op = step['op']
        assert op in ['root', 'remove', 'set_attr', 'set_text']
        if op == 'root':
            path = step['path']
            _logger.debug('selecting new root using [%s]', path)
            elements = xpath(root, path)
            if len(elements) > 1:
                raise ValueError('Root expression must not select multiple elements: ' + path)
            if len(elements) == 0:
                _logger.debug('no matches for new root, no data to extract')
                return {}
            root = elements[0]
        elif op == 'remove':
            path = step['path']
            elements = xpath(root, path)
            _logger.debug('removing %s elements using [%s]', len(elements), path)
            for element in elements:
                # XXX: could this be hazardous? parent removed in earlier iteration?
                get_parent(element).remove(element)
        elif op == 'set_attr':
            path = step['path']
            attr_name_gen = gen(step['name'])
            attr_value_gen = gen(step['value'])
            for element in xpath(root, path):
                attr_name = attr_name_gen(element)
                attr_value = attr_value_gen(element)
                _logger.debug('setting [%s] attribute to [%s] on [%s] element',
                              attr_name, attr_value, element.tag)
                element.attrib[attr_name] = attr_value
        elif op == 'set_text':
            path = step['path']
            text_gen = gen(step['text'])
            for element in xpath(root, path):
                text_value = text_gen(element)
                _logger.debug('setting text to [%s] on [%s] element', text_value, element.tag)
                element.text = text_value

    # actual extraction part
    data = {}
    for item in items:
        key_gen = gen(item['key'])
        foreach_key = item.get('foreach')
        subroots = [root] if foreach_key is None else xpath(root, foreach_key)
        for subroot in subroots:
            key = key_gen(subroot)
            value_gen = gen(item['value'])
            foreach_value = item['value'].get('foreach')
            if foreach_value is None:
                value = value_gen(subroot)
                if value:   # None from pecker, or {} from extract
                    # XXX: consider '', 0, and other non-truthy values
                    data[key] = value
            else:
                values = [value_gen(r) for r in xpath(subroot, foreach_value)]
                if values:
                    data[key] = values
    return data


def get_document(url):
    """Get the document with the given URL.

    This function will check whether the requested document has already been
    retrieved and return the cached content if possible. Note that
    cached documents are assumed to be up-to-date.

    :sig: (str) -> str
    :param url: URL to get the document from.
    :return: Content of the retrieved document.
    """
    _logger.debug('getting page [%s]', url)
    cache_dir = os.environ.get('PICULET_WEB_CACHE')
    if cache_dir is None:
        _logger.debug('cache disabled, downloading page')
        content = urlopen(url).read()
    else:
        _logger.debug('using cache dir [%s]', cache_dir)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        # PY3: os.makedirs(cache_dir, exist_ok=True)

        key = md5(url.encode('utf-8')).hexdigest()
        cache_file = os.path.join(cache_dir, key)
        if not os.path.exists(cache_file):
            _logger.debug('page not in cache, downloading and storing')
            content = urlopen(url).read()
            with open(cache_file, 'wb') as f:
                f.write(content)
        else:
            _logger.debug('using page found in cache')
            with open(cache_file, 'rb') as f:
                content = f.read()
    _logger.debug('read %s bytes', len(content))
    return decode_html(content)


def scrape(document, rules, content_format='xml'):
    """Extract data from a document according to given rules.

    :sig: (str, Mapping[str, Any], Optional[str]) -> Mapping[str, Any]
    :param document: Document to scrape.
    :param rules: Rules to use for scraping.
    :param content_format: Format of the content, XML or HTML.
    :return: Extracted data.
    """
    if content_format == 'html':
        _logger.debug('converting html document to xml')
        document = html_to_xhtml(document)
        # _logger.debug('=== CONTENT START ===\n%s\n=== CONTENT END===', document)
    root = build_tree(document)
    data = extract(root, rules['items'], pre=rules.get('pre', ()))
    return data


###########################################################
# COMMAND-LINE INTERFACE
###########################################################


def h2x(source):
    """Convert an HTML file into XHTML and print.

    :sig: (str) -> None
    :param source: Path of HTML file to convert.
    """
    _logger.debug('converting html to xhtml')
    if source == '-':
        _logger.debug('reading from stdin')
        content = sys.stdin.read()
    else:
        path = os.path.abspath(source)
        _logger.debug('reading from file [%s]', path)
        with open(path, 'rb') as f:
            content = decode_html(f.read())
    print(html_to_xhtml(content), end='')


def scrape_url(url, spec, ruleset, content_format='xml'):
    """Scrape data from a URL and print.

    :sig: (str, str, str, Optional[str]) -> None
    :param url: URL of document to scrape.
    :param spec: Path of spec file.
    :param ruleset: Selected rules from the spec.
    :param content_format: Whether the content is XML or HTML.
    """
    with open(spec) as f:
        scraper = json.loads(f.read())

    rules = scraper.get(ruleset)
    if rules is None:
        raise ValueError('Rules not found: ' + ruleset)
    _logger.debug('using rules [%s]', ruleset)

    _logger.debug('scraping url [%s]', url)
    document = get_document(url)
    data = scrape(document, rules, content_format=content_format)
    print(json.dumps(data, indent=2, sort_keys=True))


def _get_parser(prog):
    """Get a parser for command line arguments."""

    def _h2x(arguments):
        h2x(arguments.file)

    def _scrape(arguments):
        content_format = 'html' if arguments.html else 'xml'
        scrape_url(arguments.url, arguments.spec, arguments.rules,
                   content_format=content_format)

    parser = ArgumentParser(prog=prog)
    parser.add_argument('--debug', action='store_true',
                        help='enable debug messages')

    commands = parser.add_subparsers(metavar='command', dest='command')
    commands.required = True

    subparser = commands.add_parser('h2x', help='convert HTML to XHTML')
    subparser.set_defaults(func=_h2x)
    subparser.add_argument('file', help='file to convert')

    subparser = commands.add_parser('scrape', help='scrape a document')
    subparser.set_defaults(func=_scrape)
    subparser.add_argument('url', help='URL to scrape')
    subparser.add_argument('-s', '--spec', required=True,
                           help='spec file')
    subparser.add_argument('-r', '--rules', required=True,
                           help='selected rule set in spec')
    subparser.add_argument('--html', action='store_true',
                           help='document content is html')

    return parser


def main(argv=None):
    """Entry point of the command line utility.

    :sig: (Optional[List[str]]) -> None
    :param argv: Command line arguments.
    """
    argv = argv if argv is not None else sys.argv
    parser = _get_parser(prog=argv[0])
    arguments = parser.parse_args(argv[1:])

    # set debug mode
    if arguments.debug:
        logging.basicConfig(level=logging.DEBUG)
        _logger.debug('running in debug mode')

    # run the handler for the selected command
    try:
        arguments.func(arguments)
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
