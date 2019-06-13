# Copyright (C) 2014-2019 H. Turgut Uyar <uyar@tekir.org>
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

"""Module for scraping XML and HTML documents using XPath queries.

It consists of this single source file with no dependencies
other than the standard library, which makes it very easy
to integrate into applications.

For more information, please refer to the documentation:
https://piculet.tekir.org/
"""

import json
import re
import sys
from abc import ABC, abstractmethod
from argparse import ArgumentParser
from collections import deque
from contextlib import redirect_stdout
from functools import lru_cache, partial
from html import escape as html_escape
from html.parser import HTMLParser
from io import StringIO
from operator import itemgetter
from pathlib import Path as FSPath
from pkgutil import find_loader
from types import SimpleNamespace


__version__ = "2.0.0.dev2"  # sig: str


###########################################################
# HTML OPERATIONS
###########################################################


class HTMLNormalizer(HTMLParser):
    """HTML to XHTML converter.

    Other than converting the document to valid XHTML, this will
    remove unwanted tags and attributes, along with all comments
    and DOCTYPE declarations.
    """

    VOID_ELEMENTS = frozenset(  # sig: ClassVar[FrozenSet[str]]
        {
            "area",
            "base",
            "basefont",
            "bgsound",
            "br",
            "col",
            "command",
            "embed",
            "frame",
            "hr",
            "image",
            "img",
            "input",
            "isindex",
            "keygen",
            "link",
            "menuitem",
            "meta",
            "nextid",
            "param",
            "source",
            "track",
            "wbr",
        }
    )
    """Tags to handle as self-closing."""

    def __init__(self, *, omit_tags=None, omit_attrs=None):
        """Initialize this normalizer.

        :sig: (Optional[Iterable[str]], Optional[Iterable[str]]) -> None
        :param omit_tags: Tags to remove.
        :param omit_attrs: Attributes to remove.
        """
        super().__init__(convert_charrefs=True)

        self.omit_tags = set(omit_tags) if omit_tags is not None else set()  # sig: Set[str]
        self.omit_attrs = set(omit_attrs) if omit_attrs is not None else set()  # sig: Set[str]

        # stacks used during normalization
        self._open_tags = deque()
        self._open_omitted_tags = deque()

    def handle_starttag(self, tag, attrs):
        """Process the starting of a new element."""
        if tag in self.omit_tags:
            # omit starting tag
            self._open_omitted_tags.append(tag)
        if not self._open_omitted_tags:
            # stack empty -> not in omit mode
            if "@" in tag:
                # email address in angular brackets
                print("&lt;%s&gt;" % tag, end="")
                return
            if (tag == "li") and (self._open_tags[-1] == "li"):
                # opening <li> without closing previous <li>, add </li>
                self.handle_endtag("li")
            attributes = []
            for attr_name, attr_value in attrs:
                if attr_name in self.omit_attrs:
                    # omit attribute
                    continue
                if attr_value is None:
                    # add empty value for attribute
                    attr_value = ""
                markup = '%(name)s="%(value)s"' % {
                    "name": attr_name,
                    "value": html_escape(attr_value, quote=True),
                }
                attributes.append(markup)
            line = "<%(tag)s%(attrs)s%(slash)s>" % {
                "tag": tag,
                "attrs": (" " + " ".join(attributes)) if len(attributes) > 0 else "",
                "slash": "/" if tag in HTMLNormalizer.VOID_ELEMENTS else "",
            }
            print(line, end="")
            if tag not in HTMLNormalizer.VOID_ELEMENTS:
                self._open_tags.append(tag)

    def handle_endtag(self, tag):
        """Process the ending of an element."""
        if not self._open_omitted_tags:
            # stack empty -> not in omit mode
            if tag not in HTMLNormalizer.VOID_ELEMENTS:
                last = self._open_tags[-1]
                if (tag == "ul") and (last == "li"):
                    # closing <ul> without closing last <li>, add </li>
                    self.handle_endtag("li")
                if tag == last:
                    # expected end tag
                    print("</%(tag)s>" % {"tag": tag}, end="")
                    self._open_tags.pop()
                elif tag not in self._open_tags:
                    # closing tag without opening tag
                    # XXX: for <a><b></a></b>, this case gets invoked after the case below
                    pass
                elif tag == self._open_tags[-2]:
                    # unexpected closing tag, close both
                    print("</%(tag)s>" % {"tag": last}, end="")
                    print("</%(tag)s>" % {"tag": tag}, end="")
                    self._open_tags.pop()
                    self._open_tags.pop()
        elif (tag in self.omit_tags) and (tag == self._open_omitted_tags[-1]):
            # end of expected omitted tag
            self._open_omitted_tags.pop()

    def handle_data(self, data):
        """Process collected character data."""
        if not self._open_omitted_tags:
            # stack empty -> not in omit mode
            line = html_escape(data)
            print(line, end="")

    # def feed(self, data):
    #     super().feed(data)
    #     # close all remaining open tags
    #     for tag in reversed(self._open_tags):
    #         print('</%(tag)s>' % {'tag': tag}, end='')


def html_to_xhtml(document, *, omit_tags=None, omit_attrs=None):
    """Convert an HTML document to XHTML.

    :sig: (str, Optional[Iterable[str]], Optional[Iterable[str]]) -> str
    :param document: HTML document to convert.
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
# DATA EXTRACTION CLASSES
###########################################################


# sigalias: XPather = Callable[[Element], Union[Sequence[str], Sequence[Element]]]


LXML_AVAILABLE = find_loader("lxml") is not None  # sig: bool
if LXML_AVAILABLE:
    from lxml import etree as ElementTree
    from lxml.etree import Element, XPath

    xpath = lru_cache(maxsize=None)(XPath)
else:
    from xml.etree import ElementTree
    from xml.etree.ElementTree import Element

    @lru_cache(maxsize=None)
    def xpath(path):
        """Get an XPath expression that can be applied to an element.

        This is mainly needed to compensate for the lack of ``text()``
        and ``@attr`` axis queries in ElementTree XPath support.

        :sig: (str) -> XPather
        :param path: XPath expression to compile.
        :return: Evaluator that can be applied to an element.
        """
        if path[0] == "/":
            # ElementTree doesn't support absolute paths
            # TODO: handle this properly, find root of tree
            path = "." + path

        def descendant_text(element):
            # strip trailing '//text()'
            return [t for e in element.findall(path[:-8]) for t in e.itertext() if t]

        def child_text(element):
            # strip trailing '/text()'
            return [
                t
                for e in element.findall(path[:-7])
                for t in ([e.text] + [c.tail if c.tail else "" for c in e])
                if t
            ]

        def attribute(element, subpath, attr):
            result = [e.attrib.get(attr) for e in element.findall(subpath)]
            return [r for r in result if r is not None]

        if path.endswith("//text()"):
            _apply = descendant_text
        elif path.endswith("/text()"):
            _apply = child_text
        else:
            *front, last = path.split("/")
            if last.startswith("@"):
                _apply = partial(attribute, subpath="/".join(front), attr=last[1:])
            else:
                _apply = partial(Element.findall, path=path)

        return _apply


_EMPTY = {}  # sig: Dict


# sigalias: Reducer = Callable[[Sequence[str]], str]
# sigalias: PathTransformer = Callable[[str], Any]
# sigalias: MapTransformer = Callable[[Mapping], Any]
# sigalias: Transformer = Union[PathTransformer, MapTransformer]


class Extractor(ABC):
    """Abstract base extractor for getting data out of an XML element."""

    def __init__(self, *, transform=None, foreach=None):
        """Initialize this extractor.

        :sig: (Optional[Transformer], Optional[str]) -> None
        :param transform: Function to transform the extracted value.
        :param foreach: Path to apply for generating a collection of values.
        """
        self.transform = transform  # sig: Optional[Transformer]
        """Function to transform the extracted value."""

        self.foreach = xpath(foreach) if foreach is not None else None  # sig: Optional[XPather]
        """Path to apply for generating a collection of values."""

    @abstractmethod
    def apply(self, element):
        """Get the raw data from an element using this extractor.

        :sig: (Element) -> Union[str, Mapping]
        :param element: Element to apply this extractor to.
        :return: Extracted raw data.
        """

    def extract(self, element, *, transform=True):
        """Get the processed data from an element using this extractor.

        :sig: (Element, bool) -> Any
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

        :sig: (Mapping) -> Extractor
        :param item: Extractor description.
        :return: Extractor object.
        :raise ValueError: When reducer or transformer names are unknown.
        """
        transformer = item.get("transform")
        if transformer is None:
            transform = None
        else:
            transform = getattr(transformers, transformer, None)
            if transform is None:
                raise ValueError("Unknown transformer")

        foreach = item.get("foreach")

        path = item.get("path")
        if path is not None:
            reducer = item.get("reduce")
            if reducer is None:
                reduce = None
            else:
                reduce = getattr(reducers, reducer, None)
                if reduce is None:
                    raise ValueError("Unknown reducer")
            extractor = Path(path, reduce=reduce, transform=transform, foreach=foreach)
        else:
            items = item.get("items", [])
            rules = [Rule.from_map(i) for i in items]
            extractor = Rules(
                rules, section=item.get("section"), transform=transform, foreach=foreach
            )

        return extractor


class Path(Extractor):
    """An extractor for getting text out of an XML element."""

    def __init__(self, path, reduce=None, *, transform=None, foreach=None):
        """Initialize this extractor.

        :sig: (
                str,
                Optional[Reducer],
                Optional[PathTransformer],
                Optional[str]
            ) -> None
        :param path: Path to apply to get the data.
        :param reduce: Function to reduce selected texts into a single string.
        :param transform: Function to transform extracted value.
        :param foreach: Path to apply for generating a collection of data.
        """
        super().__init__(transform=transform, foreach=foreach)

        self.path = xpath(path)  # sig: XPather
        """XPath evaluator to apply to get the data."""

        if reduce is None:
            reduce = reducers.concat

        self.reduce = reduce  # sig: Reducer
        """Function to reduce selected texts into a single string."""

    def apply(self, element):
        """Apply this extractor to an element.

        :sig: (Element) -> str
        :param element: Element to apply this extractor to.
        :return: Extracted text.
        """
        selected = self.path(element)
        return self.reduce(selected) if len(selected) > 0 else None


class Rules(Extractor):
    """An extractor for getting data items out of an XML element."""

    def __init__(self, rules, *, section=None, transform=None, foreach=None):
        """Initialize this extractor.

        :sig:
            (
                Sequence[Rule],
                str,
                Optional[MapTransformer],
                Optional[str]
            ) -> None
        :param rules: Rules for generating the data items.
        :param section: Path for setting the root of this section.
        :param transform: Function to transform extracted value.
        :param foreach: Path for generating multiple items.
        """
        super().__init__(transform=transform, foreach=foreach)

        self.rules = rules  # sig: Sequence[Rule]
        """Rules for generating the data items."""

        self.section = xpath(section) if section is not None else None  # sig: Optional[XPather]
        """XPath expression for selecting a subroot for this section."""

    def apply(self, element):
        """Apply this extractor to an element.

        :sig: (Element) -> Mapping
        :param element: Element to apply the extractor to.
        :return: Extracted mapping.
        """
        if self.section is None:
            subroot = element
        else:
            subroots = self.section(element)
            if len(subroots) == 0:
                return _EMPTY
            if len(subroots) > 1:
                raise ValueError("Section path should select exactly one element")
            subroot = subroots[0]

        data = {}
        for rule in self.rules:
            extracted = rule.extract(subroot)
            data.update(extracted)
        return data if len(data) > 0 else _EMPTY


class Rule:
    """A rule describing how to get a data item out of an XML element."""

    def __init__(self, key, extractor, *, foreach=None):
        """Initialize this rule.

        :sig: (Union[str, Extractor], Extractor, Optional[str]) -> None
        :param key: Name to distinguish this data item.
        :param extractor: Extractor that will generate this data item.
        :param foreach: Path for generating multiple items.
        """
        self.key = key  # sig: Union[str, Extractor]
        """Name to distinguish this data item."""

        self.extractor = extractor  # sig: Extractor
        """Extractor that will generate this data item."""

        self.foreach = xpath(foreach) if foreach is not None else None  # sig: Optional[XPather]
        """XPath evaluator for generating multiple items."""

    @staticmethod
    def from_map(item):
        """Generate a rule from a description map.

        :sig: (Mapping) -> Rule
        :param item: Item description.
        :return: Rule object.
        """
        item_key = item["key"]
        key = item_key if isinstance(item_key, str) else Extractor.from_map(item_key)
        value = Extractor.from_map(item["value"])
        return Rule(key=key, extractor=value, foreach=item.get("foreach"))

    def extract(self, element):
        """Extract data out of an element using this rule.

        :sig: (Element) -> Mapping
        :param element: Element to extract the data from.
        :return: Extracted data.
        """
        data = {}
        subroots = [element] if self.foreach is None else self.foreach(element)
        for subroot in subroots:
            key = self.key if isinstance(self.key, str) else self.key.extract(subroot)
            if key is None:
                continue

            if self.extractor.foreach is None:
                value = self.extractor.extract(subroot)
                if (value is None) or (value is _EMPTY):
                    continue
                data[key] = value
            else:
                # don't try to transform list items by default, it might waste a lot of time
                raw_values = [
                    self.extractor.extract(r, transform=False)
                    for r in self.extractor.foreach(subroot)
                ]
                values = [v for v in raw_values if (v is not None) and (v is not _EMPTY)]
                if len(values) == 0:
                    continue
                data[key] = (
                    values
                    if self.extractor.transform is None
                    else list(map(self.extractor.transform, values))
                )
        return data


###########################################################
# PREPROCESSING OPERATIONS
###########################################################


def remove_elements(root, path):
    """Remove selected elements from the tree.

    :sig: (Element, str) -> None
    :param root: Root element of the tree.
    :param path: XPath to select the elements to remove.
    """
    if LXML_AVAILABLE:
        get_parent = ElementTree._Element.getparent
    else:
        # ElementTree doesn't support parent queries, so we'll build a map for it
        get_parent = root.attrib.get("_get_parent")
        if get_parent is None:
            get_parent = {e: p for p in root.iter() for e in p}.get
            root.attrib["_get_parent"] = get_parent
    elements = xpath(path)(root)
    if len(elements) > 0:
        for element in elements:
            # XXX: could this be hazardous? parent removed in earlier iteration?
            get_parent(element).remove(element)


def set_element_attr(root, path, name, value):
    """Set an attribute for selected elements.

    :sig:
        (
            Element,
            str,
            Union[str, Mapping],
            Union[str, Mapping]
        ) -> None
    :param root: Root element of the tree.
    :param path: XPath to select the elements to set attributes for.
    :param name: Description for name generation.
    :param value: Description for value generation.
    """
    elements = xpath(path)(root)
    for element in elements:
        attr_name = name if isinstance(name, str) else Extractor.from_map(name).extract(element)
        if attr_name is None:
            continue

        attr_value = (
            value if isinstance(value, str) else Extractor.from_map(value).extract(element)
        )
        if attr_value is None:
            continue

        element.attrib[attr_name] = attr_value


def set_element_text(root, path, text):
    """Set the text for selected elements.

    :sig: (Element, str, Union[str, Mapping]) -> None
    :param root: Root element of the tree.
    :param path: XPath to select the elements to set attributes for.
    :param text: Description for text generation.
    """
    elements = xpath(path)(root)
    for element in elements:
        element_text = (
            text if isinstance(text, str) else Extractor.from_map(text).extract(element)
        )
        # note that the text can be None in which case the existing text will be cleared
        element.text = element_text


###########################################################
# REGISTRIES
###########################################################


preprocessors = SimpleNamespace(  # sig: SimpleNamespace
    remove=remove_elements, set_attr=set_element_attr, set_text=set_element_text
)
"""Predefined preprocessors."""


reducers = SimpleNamespace(  # sig: SimpleNamespace
    first=itemgetter(0),
    concat=partial(str.join, ""),
    clean=lambda xs: re.sub(r"\s+", " ", "".join(xs).replace("\xa0", " ")).strip(),
    normalize=lambda xs: re.sub(r"[^a-z0-9_]", "", "".join(xs).lower().replace(" ", "_")),
)
"""Predefined reducers."""

transformers = SimpleNamespace(  # sig: SimpleNamespace
    int=int,
    float=float,
    bool=bool,
    len=len,
    lower=str.lower,
    upper=str.upper,
    capitalize=str.capitalize,
    lstrip=str.lstrip,
    rstrip=str.rstrip,
    strip=str.strip,
)
"""Predefined transformers."""


###########################################################
# MAIN API
###########################################################


def build_tree(document, *, lxml_html=False):
    """Build a tree from an XML document.

    :sig: (str, bool) -> Element
    :param document: XML document to build the tree from.
    :param lxml_html: Use the lxml.html builder if available.
    :return: Root element of the XML tree.
    """
    if lxml_html:
        if not LXML_AVAILABLE:
            raise RuntimeError("LXML not available")
        import lxml.html

        fromstring = lxml.html.fromstring
    else:
        fromstring = ElementTree.fromstring
    return fromstring(document)


def preprocess(root, pre):
    """Process a tree before starting extraction.

    :sig: (Element, Sequence[Mapping]) -> None
    :param root: Root of tree to process.
    :param pre: Descriptions for processing operations.
    """
    for step in pre:
        op = step["op"]
        if op == "remove":
            remove_elements(root, step["path"])
        elif op == "set_attr":
            set_element_attr(root, step["path"], name=step["name"], value=step["value"])
        elif op == "set_text":
            set_element_text(root, step["path"], text=step["text"])
        else:
            raise ValueError("Unknown preprocessing operation")


def extract(element, items, *, section=None):
    """Extract data from an XML element.

    :sig:
        (
            Element,
            Sequence[Mapping],
            Optional[str]
        ) -> Mapping
    :param element: Element to extract the data from.
    :param items: Descriptions for extracting items.
    :param section: Path to select the root element for these items.
    :return: Extracted data.
    """
    rules = Rules([Rule.from_map(item) for item in items], section=section)
    return rules.extract(element)


def scrape(document, spec, *, lxml_html=False):
    """Extract data from a document after optionally preprocessing it.

    :sig: (str, Mapping, bool) -> Mapping
    :param document: Document to scrape.
    :param spec: Extraction specification.
    :param lxml_html: Use the lxml.html builder if available.
    :return: Extracted data.
    """
    root = build_tree(document, lxml_html=lxml_html)
    pre = spec.get("pre")
    if pre is not None:
        preprocess(root, pre)
    data = extract(root, spec.get("items"), section=spec.get("section"))
    return data


###########################################################
# COMMAND-LINE INTERFACE
###########################################################


YAML_AVAILABLE = find_loader("strictyaml") is not None  # sig: bool


def load_spec(path):
    """Load an extraction specification from a file.

    :sig: (FSPath) -> Mapping
    :param path: Path of specification file.
    :return: Loaded specification.
    """
    if path.suffix in {".yaml", ".yml"}:
        if not YAML_AVAILABLE:
            raise RuntimeError("YAML support not available")
        import strictyaml

        spec_loader = lambda s: strictyaml.load(s).data
    else:
        spec_loader = json.loads

    spec_content = path.read_text(encoding="utf-8")
    return spec_loader(spec_content)


def main(argv=None):
    """Entry point of the command line utility.

    :sig: (Optional[List[str]]) -> None
    :param argv: Command line arguments.
    """
    parser = ArgumentParser(prog="piculet", description="extract data from XML/HTML")
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
    parser.add_argument("--html", action="store_true", help="document is in HTML format")

    command = parser.add_mutually_exclusive_group(required=True)
    command.add_argument("-s", "--spec", help="spec file")
    command.add_argument("--h2x", action="store_true", help="convert HTML to XHTML")

    argv = argv if argv is not None else sys.argv
    arguments = parser.parse_args(argv[1:])

    try:
        content = sys.stdin.read()
        if arguments.h2x:
            print(html_to_xhtml(content), end="")
        else:
            spec = load_spec(FSPath(arguments.spec))
            if arguments.html:
                content = html_to_xhtml(content)
            data = scrape(content, spec)
            print(json.dumps(data, indent=2, sort_keys=True))
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
