# Copyright (C) 2014-2018 H. Turgut Uyar <uyar@tekir.org>
#
# Piculet is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Piculet is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Piculet.  If not, see <http://www.gnu.org/licenses/>.

"""Piculet is a module for extracting data from XML documents using XPath queries.

It can also scrape web pages by first converting the HTML source into XHTML.
Piculet consists of this single source file with no dependencies other than
the standard library, which makes it very easy to integrate into applications.

For more details, please refer to the documentation: https://piculet.readthedocs.io/
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import logging
import os
import re
import sys
from argparse import ArgumentParser
from collections import deque
from functools import partial
from operator import itemgetter
from pkgutil import find_loader


PY3 = sys.version_info >= (3, 0)
PY34 = sys.version_info >= (3, 4)


if not PY3:
    str, bytes = unicode, str


if not PY3:
    from cgi import escape as html_escape
    from HTMLParser import HTMLParser
    from StringIO import StringIO
    from urllib2 import urlopen
else:
    from html import escape as html_escape
    from html.parser import HTMLParser
    from io import StringIO
    from urllib.request import urlopen


if not PY3:
    class SimpleNamespace:
        """A simple, attribute-based namespace."""

        def __init__(self, **kwargs):
            """Construct a new namespace."""
            self.__dict__.update(kwargs)

        def __eq__(self, other):
            """Check whether this namespace is equal to another namespace."""
            return self.__dict__ == other.__dict__
else:
    from types import SimpleNamespace


if not PY34:
    from contextlib import contextmanager

    @contextmanager
    def redirect_stdout(new_stdout):
        """Context manager for temporarily redirecting stdout."""
        old_stdout, sys.stdout = sys.stdout, new_stdout
        try:
            yield new_stdout
        finally:
            sys.stdout = old_stdout
else:
    from contextlib import redirect_stdout


_logger = logging.getLogger(__name__)


###########################################################
# HTML OPERATIONS
###########################################################


# TODO: this is too fragile
_CHARSET_TAGS = [
    b'<meta http-equiv="content-type" content="text/html; charset=',
    b'<meta charset="'
]


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
        for tag in _CHARSET_TAGS:
            start = content.find(tag)
            if start >= 0:
                charset_start = start + len(tag)
                charset_end = content.find(b'"', charset_start)
                charset = content[charset_start:charset_end].decode('ascii')
                _logger.debug('charset found in "meta": "%s"', charset)
                break
        else:
            _logger.debug('charset not found, using fallback: "%s"', fallback_charset)
            charset = fallback_charset
    _logger.debug('decoding for charset: "%s"', charset)
    return content.decode(charset)


class HTMLNormalizer(HTMLParser):
    """HTML cleaner and XHTML convertor.

    DOCTYPE declarations and comments are removed.
    """

    SELF_CLOSING_TAGS = {'br', 'hr', 'img', 'input', 'link', 'meta'}
    """Tags to handle as self-closing."""

    def __init__(self, omit_tags=None, omit_attrs=None):
        """Initialize this normalizer.

        :sig: (Optional[Iterable[str]], Optional[Iterable[str]]) -> None
        :param omit_tags: Tags to remove, along with all their content.
        :param omit_attrs: Attributes to remove.
        """
        if not PY3:
            HTMLParser.__init__(self)
        elif not PY34:
            super().__init__()
        else:
            super().__init__(convert_charrefs=True)

        self.omit_tags = set(omit_tags) if omit_tags is not None else set()     # sig: Set[str]
        self.omit_attrs = set(omit_attrs) if omit_attrs is not None else set()  # sig: Set[str]

        # stacks used during normalization
        self._open_tags = deque()
        self._open_omitted_tags = deque()

    def handle_starttag(self, tag, attrs):
        """Process the starting of a new element."""
        if tag in self.omit_tags:
            _logger.debug('omitting: "%s"', tag)
            self._open_omitted_tags.append(tag)
        if not self._open_omitted_tags:
            # stack empty -> not in omit mode
            if (tag == 'li') and (self._open_tags[-1] == 'li'):
                _logger.debug('opened "li" without closing previous "li", adding closing tag')
                self.handle_endtag('li')
            attributes = []
            for attr_name, attr_value in attrs:
                if attr_name in self.omit_attrs:
                    _logger.debug('omitting "%s" attribute of "%s"', attr_name, tag)
                    continue
                if attr_value is None:
                    _logger.debug('no value for "%s" attribute of "%s", adding empty value',
                                  attr_name, tag)
                    attr_value = ''
                markup = '%(name)s="%(value)s"' % {
                    'name': attr_name,
                    'value': html_escape(attr_value, quote=True)
                }
                attributes.append(markup)
            line = '<%(tag)s%(attrs)s%(slash)s>' % {
                'tag': tag,
                'attrs': (' ' + ' '.join(attributes)) if len(attributes) > 0 else '',
                'slash': ' /' if tag in self.SELF_CLOSING_TAGS else ''
            }
            print(line, end='')
            if tag not in self.SELF_CLOSING_TAGS:
                self._open_tags.append(tag)

    def handle_endtag(self, tag):
        """Process the ending of an element."""
        if not self._open_omitted_tags:
            # stack empty -> not in omit mode
            if tag not in self.SELF_CLOSING_TAGS:
                last = self._open_tags[-1]
                if (tag == 'ul') and (last == 'li'):
                    _logger.debug('closing "ul" without closing last "li", adding closing tag')
                    self.handle_endtag('li')
                if tag == last:
                    # expected end tag
                    print('</%(tag)s>' % {'tag': tag}, end='')
                    self._open_tags.pop()
                elif tag not in self._open_tags:
                    _logger.debug('closing tag "%s" without opening tag', tag)
                    # XXX: for <a><b></a></b>, this case gets invoked after the case below
                elif tag == self._open_tags[-2]:
                    _logger.debug('unexpected closing tag "%s" instead of "%s", closing both',
                                  tag, last)
                    print('</%(tag)s>' % {'tag': last}, end='')
                    print('</%(tag)s>' % {'tag': tag}, end='')
                    self._open_tags.pop()
                    self._open_tags.pop()
        elif (tag in self.omit_tags) and (tag == self._open_omitted_tags[-1]):
            # end of expected omitted tag
            self._open_omitted_tags.pop()

    def handle_data(self, data):
        """Process collected character data."""
        if not self._open_omitted_tags:
            # stack empty -> not in omit mode
            print(html_escape(data), end='')

    def handle_entityref(self, name):
        """Process an entity reference."""
        # XXX: doesn't get called if convert_charrefs=True
        ref = self.unescape('&' + name + ';')
        print('&#%d;' % ord(ref))

    def handle_charref(self, name):
        """Process a character reference."""
        # XXX: doesn't get called if convert_charrefs=True
        print('&#' + name + ';', end='')

    # def feed(self, data):
        # super().feed(data)
        # # close all remaining open tags
        # for tag in reversed(self._open_tags):
        #     print('</%(tag)s>' % {'tag': tag}, end='')


def html_to_xhtml(document, omit_tags=None, omit_attrs=None):
    """Clean HTML and convert to XHTML.

    :sig: (str, Optional[Iterable[str]], Optional[Iterable[str]]) -> str
    :param document: HTML document to clean and convert.
    :param omit_tags: Tags to exclude from the output.
    :param omit_attrs: Attributes to exclude from the output.
    :return: Normalized XHTML content.
    """
    out = StringIO()
    normalizer = HTMLNormalizer(omit_tags=omit_tags, omit_attrs=omit_attrs)
    with redirect_stdout(out):
        normalizer.feed(document)
    return out.getvalue()


###########################################################
# DATA EXTRACTION OPERATIONS
###########################################################


_USE_LXML = find_loader('lxml') is not None
if _USE_LXML:
    _logger.info('using lxml')
    from lxml import etree as ElementTree
else:
    from xml.etree import ElementTree


def build_tree(document, force_html=False):
    """Build a tree from an XML document.

    :sig: (str, Optional[bool]) -> ElementTree.Element
    :param document: XML document to build the tree from.
    :param force_html: Force to parse from HTML without converting.
    :return: Root node of the XML tree.
    """
    content = document if PY3 else document.encode('utf-8')
    if _USE_LXML and force_html:
        _logger.info('using lxml html builder')
        import lxml.html
        return lxml.html.fromstring(content)
    return ElementTree.fromstring(content)


def xpath_etree(element, path):
    """Apply an XPath expression to an element.

    This function is mainly needed to compensate for the lack of ``text()``
    and ``@attr`` axis queries in ElementTree XPath support.

    :sig: (ElementTree.Element, str) -> Union[Sequence[str], Sequence[ElementTree.Element]]
    :param element: Element to apply the expression to.
    :param path: XPath expression to apply.
    :return: Elements or strings resulting from the query.
    """
    if path[0] == '/':
        # ElementTree doesn't support absolute paths
        # TODO: handle this properly, find root of tree
        path = '.' + path

    if path.endswith('//text()'):
        return [t for e in element.findall(path[:-8]) for t in e.itertext() if t]

    if path.endswith('/text()'):
        return [t for e in element.findall(path[:-7])
                for t in ([e.text] + [c.tail if c.tail else '' for c in e]) if t]

    path_tokens = path.split('/')
    epath, last_step = path_tokens[:-1], path_tokens[-1]
    # PY3: *epath, last_step = path.split('/')
    if last_step.startswith('@'):
        result = [e.attrib.get(last_step[1:]) for e in element.findall('/'.join(epath))]
        return [r for r in result if r is not None]

    return element.findall(path)


xpath = xpath_etree if not _USE_LXML else ElementTree._Element.xpath


_REDUCERS = {
    'first': itemgetter(0),
    'concat': partial(str.join, ''),
    'clean': lambda xs: re.sub('\s+', ' ', ''.join(xs).replace('\xa0', ' ')).strip(),
    'normalize': lambda xs: re.sub('[^a-z0-9_]', '', ''.join(xs).lower().replace(' ', '_'))
}

reducers = SimpleNamespace(**_REDUCERS)
"""Predefined reducers."""


_EMPTY = {}     # empty result singleton


class Extractor:
    """An extractor for getting data out of an XML element."""

    def __init__(self, transform=None, foreach=None):
        """Initialize this extractor.

        :sig:
            (
                Optional[Callable[[Union[str, Mapping[str, Any]]], Any]],
                Optional[str]
            ) -> None
        :param transform: Function to transform extracted value.
        :param foreach: Path to apply for generating a collection of values.
        """
        self.transform = transform  # sig: Optional[Callable[[Union[str, Mapping[str, Any]]], Any]]
        """Function to transform extracted value."""

        self.foreach = foreach      # sig: Optional[str]
        """Path to apply for generating a collection of values."""

    def apply(self, element):
        """Get the raw data from an element using this extractor.

        :sig: (ElementTree.Element) -> Union[str, Mapping[str, Any]]
        :param element: Element to apply this extractor to.
        :return: Extracted raw data.
        """
        raise NotImplementedError('Extractors must implement this method')

    def extract(self, element, transform=True):
        """Get the processed data from an element using this extractor.

        :sig: (ElementTree.Element, Optional[bool]) -> Any
        :param element: Element to extract the data from.
        :param transform: Whether the transformation will be applied or not.
        :return: Extracted and optionally transformed data.
        """
        value = self.apply(element)
        if (value is None) or (value is _EMPTY) or (not transform):
            return value
        return value if self.transform is None else self.transform(value)

    @staticmethod
    def from_map(item):
        """Generate an extractor from a description map.

        :sig: (Mapping[str, Any]) -> Extractor
        :param item: Extractor description.
        :return: Extractor object.
        """
        path = item.get('path')
        if path is not None:
            reduce = item.get('reduce', _REDUCERS.get(item.get('reducer')))
            extractor = Path(path, reduce)
        else:
            items = item.get('items')
            # TODO: check for None
            subrules = [Rule.from_map(i) for i in items]
            extractor = Rules(subrules)

        extractor.transform = item.get('transform')
        extractor.foreach = item.get('foreach')
        return extractor


class Path(Extractor):
    """An extractor for getting text out of an XML element."""

    def __init__(self, path, reduce=None, transform=None, foreach=None):
        """Initialize this extractor.

        :sig:
            (
                str,
                Optional[Callable[[Sequence[str]], str]],
                Optional[Callable[[str], Any]],
                Optional[str]
            ) -> None
        :param path: Path to apply to get the data.
        :param reduce: Function to reduce selected texts into a single string.
        :param transform: Function to transform extracted value.
        :param foreach: Path to apply for generating a collection of data.
        """
        if not PY3:
            Extractor.__init__(self, transform=transform, foreach=foreach)
        else:
            super().__init__(transform=transform, foreach=foreach)

        self.path = path            # sig: str
        """Path to apply to get the data."""

        if reduce is None:
            reduce = reducers.concat

        self.reduce = reduce        # sig: Callable[[Sequence[str]], str]
        """Function to reduce selected texts into a single string."""

    def apply(self, element):
        """Apply this extractor to an element.

        :sig: (ElementTree.Element) -> str
        :param element: Element to apply this extractor to.
        :return: Extracted text.
        """
        # _logger.debug('applying path "%s" on "%s" element', self.path, element.tag)
        selected = xpath(element, self.path)
        if len(selected) == 0:
            # _logger.debug('no match')
            value = None
        else:
            # _logger.debug('selected nodes: "%s"', selected)
            value = self.reduce(selected)
            # _logger.debug('reduced using "%s": "%s"', self.reduce, value)
        return value


class Rules(Extractor):
    """An extractor for getting data items out of an XML element."""

    def __init__(self, subrules, transform=None, foreach=None):
        """Initialize this extractor.

        :sig:
            (
                Iterable[Rule],
                Optional[Callable[[Mapping[str, Any]], Any]],
                Optional[str]
            ) -> None
        :param subrules: Rules for generating subitems.
        :param transform: Function to transform extracted value.
        :param foreach: Path to apply for generating a collection of data.
        """
        if not PY3:
            Extractor.__init__(self, transform=transform, foreach=foreach)
        else:
            super().__init__(transform=transform, foreach=foreach)

        self.subrules = subrules    # sig: Iterable[Rule]
        """Rules for generating subitems."""

    def apply(self, element):
        """Apply this extractor to an element.

        :sig: (ElementTree.Element) -> Mapping[str, Any]
        :param element: Element to apply the extractor to.
        :return: Extracted mapping.
        """
        if element is None:
            return _EMPTY

        data = {}
        for rule in self.subrules:
            extracted = rule.extract(element)
            data.update(extracted)
        return data if len(data) > 0 else _EMPTY


class Rule:
    """A rule describing how to get a piece of data out of an XML element."""

    def __init__(self, key, extractor, section=None):
        """Initialize this rule.

        :sig: (Union[str, Extractor], Extractor, Optional[str]) -> None
        :param key: Name to distinguish the extracted data.
        :param extractor: Extractor that will get the data.
        :param section: Path to select section nodes.
        """
        self.key = key              # sig: Union[str, Extractor]
        """Name to distinguish this piece of data."""

        self.extractor = extractor  # sig: Extractor
        """Extractor that will get this piece of data."""

        self.section = section      # sig: Optional[str]
        """Path to select section nodes."""

    @staticmethod
    def from_map(item):
        """Generate a rule from a description map.

        :sig: (Mapping[str, Any]) -> Rule
        :param item: Rule description.
        :return: Rule object.
        """
        item_key = item['key']
        key = item_key if isinstance(item_key, str) else Extractor.from_map(item_key)
        value = Extractor.from_map(item['value'])
        return Rule(key=key, extractor=value, section=item.get('section'))

    def extract(self, element):
        """Extract data out of an element using this rule.

        :sig: (ElementTree.Element) -> Mapping[str, Any]
        :param element: Element to extract the data from.
        :return: Extracted data.
        """
        data = {}
        sections = [element] if self.section is None else xpath(element, self.section)
        for section in sections:
            # _logger.debug('setting section node to: "%s"', section.tag)

            key = self.key if isinstance(self.key, str) else self.key.extract(section)
            if key is None:
                # _logger.debug('no value generated for key name')
                continue
            # _logger.debug('extracting key: "%s"', key)

            if self.extractor.foreach is None:
                value = self.extractor.extract(section)
                if (value is None) or (value is _EMPTY):
                    # _logger.debug('no value generated for key')
                    continue
                data[key] = value
                # _logger.debug('extracted value for "%s": "%s"', key, data[key])
            else:
                # don't try to transform list items by default, it might waste a lot of time
                raw_values = [self.extractor.extract(r, transform=False)
                              for r in xpath(section, self.extractor.foreach)]
                values = [v for v in raw_values if (v is not None) and (v is not _EMPTY)]
                if len(values) == 0:
                    # _logger.debug('no items found in list')
                    continue
                data[key] = values if self.extractor.transform is None else \
                    list(map(self.extractor.transform, values))
                # _logger.debug('extracted value for "%s": "%s"', key, data[key])
        return data


def extract(element, items):
    """Extract data from an XML element.

    :sig: (ElementTree.Element, Iterable[Mapping[str, Any]]) -> Mapping[str, Any]
    :param element: Element to extract the data from.
    :param items: Rules that specify how to extract the data items.
    :return: Extracted data.
    """
    rules = Rules([Rule.from_map(item) for item in items])
    return rules.extract(element)


def set_root_node(root, path):
    """Change the root node of the tree.

    :sig: (ElementTree.Element, str) -> ElementTree.Element
    :param root: Current root of the tree.
    :param path: XPath to select the new root.
    :return: New root node of the tree.
    """
    _logger.debug('selecting new root using path: "%s"', path)
    elements = xpath(root, path)

    if len(elements) != 1:
        _logger.debug('%s elements match for new root', len(elements))
        return None

    root = elements[0]
    _logger.debug('setting root to "%s" element', root.tag)

    if _USE_LXML:
        root = ElementTree.fromstring(ElementTree.tostring(root))

    return root


def remove_nodes(root, path):
    """Remove selected nodes from the tree.

    :sig: (ElementTree.Element, str) -> ElementTree.Element
    :param root: Root node of the tree.
    :param path: XPath to select the nodes to remove.
    :return: Root node of the tree.
    """
    elements = xpath(root, path)
    _logger.debug('removing %s elements using path: "%s"', len(elements), path)

    if len(elements) > 0:
        # ElementTree doesn't support parent queries, so we'll build a map for it
        get_parent = ElementTree._Element.getparent if _USE_LXML else \
            {e: p for p in root.iter() for e in p}.get

        for element in elements:
            _logger.debug('removing element: "%s"', element.tag)
            # XXX: could this be hazardous? parent removed in earlier iteration?
            get_parent(element).remove(element)
    return root


def set_node_attr(root, path, name, value):
    """Set an attribute for selected nodes.

    :sig:
        (
            ElementTree.Element,
            str,
            Union[str, Mapping[str, Any]],
            Union[str, Mapping[str, Any]]
        ) -> ElementTree.Element
    :param root: Root node of the tree.
    :param path: XPath to select the nodes to set attributes for.
    :param name: Description for name generation.
    :param value: Description for value generation.
    :return: Root node of the tree.
    """
    elements = xpath(root, path)
    _logger.debug('updating %s elements using path: "%s"', len(elements), path)
    for element in elements:
        attr_name = name if isinstance(name, str) else \
            Extractor.from_map(name).extract(element)
        if attr_name is None:
            _logger.debug('no attribute name generated for "%s" element', element.tag)
            continue

        attr_value = value if isinstance(value, str) else \
            Extractor.from_map(value).extract(element)
        if attr_value is None:
            _logger.debug('no attribute value generated for "%s" element', element.tag)
            continue

        _logger.debug('setting "%s" attribute to "%s" on "%s" element',
                      attr_name, attr_value, element.tag)
        element.attrib[attr_name] = attr_value
    return root


def set_node_text(root, path, text):
    """Set the text for selected nodes.

    :sig:
        (
            ElementTree.Element,
            str,
            Union[str, Mapping[str, Any]]
        ) -> ElementTree.Element
    :param root: Root node of the tree.
    :param path: XPath to select the nodes to set attributes for.
    :param text: Description for text generation.
    :return: Root node of the tree.
    """
    elements = xpath(root, path)
    _logger.debug('updating %s elements using path: "%s"', len(elements), path)
    for element in elements:
        node_text = text if isinstance(text, str) else Extractor.from_map(text).extract(element)
        # note that the text can be None in which case the existing text will be cleared
        _logger.debug('setting text to "%s" on "%s" element', node_text, element.tag)
        element.text = node_text
    return root


_PREPROCESSORS = {
    'root': set_root_node,
    'remove': remove_nodes,
    'set_attr': set_node_attr,
    'set_text': set_node_text
}


def preprocess(root, pre):
    """Process a tree before starting extraction.

    :sig: (ElementTree.Element, Iterable[Mapping[str, Any]]) -> ElementTree.Element
    :param root: Root of tree to process.
    :param pre: Preprocessing operations.
    :return: Root of preprocessed tree.
    """
    for step in pre:
        op = step['op']
        func = _PREPROCESSORS.get(op)
        root = func(root, **{k: v for k, v in step.items() if k != 'op'})
        if root is None:
            break
    return root


def scrape(document, items, pre=None):
    """Extract data from a document according to given rules.

    :sig: (str, Mapping[str, Any], Optional[Mapping[str, Any]]) -> Mapping[str, Any]
    :param document: Document to scrape.
    :param items: Rules to use for scraping.
    :param pre: Preprocessing operations.
    :return: Extracted data.
    """
    root = build_tree(document)
    if pre is not None:
        root = preprocess(root, pre)
    data = extract(root, items)
    return data


###########################################################
# COMMAND-LINE INTERFACE
###########################################################


def h2x(source):
    """Convert an HTML file into XHTML and print.

    :sig: (str) -> None
    :param source: Path of HTML file to convert.
    """
    if source == '-':
        _logger.debug('reading from stdin')
        content = sys.stdin.read()
    else:
        _logger.debug('reading from file: "%s"', os.path.abspath(source))
        with open(source, 'rb') as f:
            content = decode_html(f.read())
    print(html_to_xhtml(content), end='')


def scrape_document(address, spec, content_format='xml'):
    """Scrape data from a file path or a URL and print.

    :sig: (str, str, Optional[str]) -> None
    :param address: File path or URL of document to scrape.
    :param spec: Path of spec file.
    :param content_format: Whether the content is XML or HTML.
    """
    _logger.debug('loading spec from file: "%s"', os.path.abspath(spec))
    with open(spec) as f:
        spec_map = json.loads(f.read())

    if address.startswith(('http://', 'https://')):
        _logger.debug('loading url: "%s"', address)
        with urlopen(address) as f:
            content = f.read()
    else:
        _logger.debug('loading file: "%s"', os.path.abspath(address))
        with open(address, 'rb') as f:
            content = f.read()
    document = decode_html(content)

    if content_format == 'html':
        _logger.debug('converting html document to xhtml')
        document = html_to_xhtml(document)
        # _logger.debug('=== CONTENT START ===\n%s\n=== CONTENT END===', document)

    data = scrape(document, spec_map.get('items'), pre=spec_map.get('pre'))
    print(json.dumps(data, indent=2, sort_keys=True))


def make_parser(prog):
    """Build a parser for command line arguments."""
    parser = ArgumentParser(prog=prog)
    parser.add_argument('--version', action='version', version='%(prog)s 1.0b5')
    parser.add_argument('--debug', action='store_true', help='enable debug messages')

    commands = parser.add_subparsers(metavar='command', dest='command')
    commands.required = True

    h2x_parser = commands.add_parser('h2x', help='convert HTML to XHTML')
    h2x_parser.add_argument('file', help='file to convert')
    h2x_parser.set_defaults(func=lambda a: h2x(a.file))

    scrape_parser = commands.add_parser('scrape', help='scrape a document')
    scrape_parser.add_argument('document', help='file path or URL of document to scrape')
    scrape_parser.add_argument('-s', '--spec', required=True, help='spec file')
    scrape_parser.add_argument('--html', action='store_true', help='document is in HTML format')
    scrape_parser.set_defaults(func=lambda a: scrape_document(
        a.document, a.spec, content_format='html' if a.html else 'xml'
    ))

    return parser


def main(argv=None):
    """Entry point of the command line utility.

    :sig: (Optional[List[str]]) -> None
    :param argv: Command line arguments.
    """
    argv = argv if argv is not None else sys.argv
    parser = make_parser(prog='piculet')
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
