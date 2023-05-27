# Copyright (C) 2014-2023 H. Turgut Uyar <uyar@tekir.org>
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
other than the standard library.
If available, it will make use of the lxml package
for improved performance and better XPath support.

For more information, please refer to the documentation:
https://piculet.readthedocs.io/
"""


__version__ = "2.0.0a2"


import json
import pathlib
import re
import sys
from abc import ABC, abstractmethod
from argparse import ArgumentParser
from contextlib import redirect_stdout
from functools import lru_cache, partial
from html import escape as html_escape
from html.parser import HTMLParser
from importlib.util import find_spec
from io import StringIO
from itertools import dropwhile
from types import MappingProxyType, SimpleNamespace
from typing import Any, Callable, FrozenSet, List, Mapping, MutableMapping, \
    Sequence, Union
from xml.etree import ElementTree
from xml.etree.ElementTree import Element


_LXML_AVAILABLE = find_spec("lxml") is not None
if _LXML_AVAILABLE:
    import lxml.etree
    import lxml.html


############################################################
# HTML OPERATIONS
############################################################


class HTMLNormalizer(HTMLParser):
    """HTML to XML convertor.

    This will remove all comments and DOCTYPE declarations.
    """

    VOID_ELEMENTS: FrozenSet[str] = frozenset({
        "area", "base", "br", "col", "command", "embed", "hr", "img", "input",
        "keygen", "link", "meta", "param", "source", "track", "wbr",
    })

    def handle_starttag(self, tag, attrs):
        print(f"<{tag}", end="")
        for name, value in attrs:
            value = html_escape(value, quote=True) if value is not None else ""
            print(f' {name}="{value}"', end="")
        if tag in HTMLNormalizer.VOID_ELEMENTS:
            print("/", end="")
        print(">", end="")

    def handle_endtag(self, tag):
        print(f"</{tag}>", end="")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data):
        print(html_escape(data), end="")


def html_to_xml(document: str, *,
                parser: Union[HTMLNormalizer, None] = None) -> str:
    """Convert an HTML document into XML.

    :param document: Document to convert.
    :param parser: Parser to handle the conversion.
    :return: Converted document.
    """
    if parser is None:
        parser = HTMLNormalizer()
    out = StringIO()
    with redirect_stdout(out):
        parser.feed(document)
    return out.getvalue()


############################################################
# ELEMENTTREE-LXML COMPATIBILITY
############################################################


def build_tree(document: str, *, html: bool = False) -> Element:
    """Build a tree from an XML document.

    :param document: XML document to build the tree from.
    :param html: Whether the document is in HTML format.
    :return: Root element of the XML tree.
    """
    if _LXML_AVAILABLE:
        fromstring = lxml.html.fromstring if html else lxml.etree.fromstring
        return fromstring(document)
    else:
        if html:
            document = html_to_xml(document)
        root = ElementTree.fromstring(document)

        # ElementTree doesn't support absolute and parent queries
        # so we add attributes for root and parent
        root.set("__root__", root)  # type: ignore
        for parent in root.iter():
            for element in parent:
                element.set("__root__", root)  # type: ignore
                element.set("__parent__", parent)  # type: ignore

        return root


get_root: Callable[[Element], Element]
get_parent: Callable[[Element], Element]

if _LXML_AVAILABLE:
    get_root = lambda e: lxml.etree._Element.getroottree(e).getroot()
    get_parent = lxml.etree._Element.getparent
else:
    get_root = partial(Element.get, key="__root__")  # type: ignore
    get_parent = partial(Element.get, key="__parent__")  # type: ignore


XPath = Callable[[Element], Union[Sequence[str], Sequence[Element]]]


@lru_cache(maxsize=None)
def xpath(path: str) -> XPath:
    """Get an XPath evaluator that can be applied to an element.

    This is needed to compensate for the lack of some features
    in ElementTree XPath support.
    """
    if _LXML_AVAILABLE:
        return lxml.etree.XPath(path)

    preps: List[Callable[[Element], Element]] = []
    if path[0] == "/":
        # ElementTree doesn't support absolute paths
        preps.append(get_root)
        path = "." + path

    # ElementTree doesn't support paths starting with a parent
    if path.startswith(".."):
        path_steps = path.split("/")
        down_steps = list(dropwhile(lambda x: x == "..", path_steps))
        for _ in range(len(path_steps) - len(down_steps)):
            preps.append(get_parent)
        path = "./" + "/".join(down_steps)

    def prep(element: Element) -> Union[Element, None]:
        for stage in preps:
            element = stage(element)
            if element is None:
                break
        return element

    def descendant_text(element: Element) -> Sequence[str]:
        start: Union[Element, None] = prep(element)
        if start is None:
            return []

        # strip trailing '//text()'
        return [
            t
            for e in start.findall(path[:-8])
            for t in e.itertext()
            if t
        ]

    def child_text(element: Element) -> Sequence[str]:
        start: Union[Element, None] = prep(element)
        if start is None:
            return []

        # strip trailing '/text()'
        return [
            t
            for e in start.findall(path[:-7])
            for t in ([e.text] + [c.tail if c.tail else "" for c in e])
            if t
        ]

    def attribute(element: Element, path: str, attr: str) -> Sequence[str]:
        start: Union[Element, None] = prep(element)
        if start is None:
            return []
        result = [e.get(attr) for e in start.findall(path)]
        return [r for r in result if r is not None]

    def etree(element: Element, path: str) -> Sequence[Element]:
        start: Union[Element, None] = prep(element)
        return start.findall(path) if start is not None else []

    if path.endswith("//text()"):
        return descendant_text
    elif path.endswith("/text()"):
        return child_text
    else:
        *front, last = path.split("/")
        if last.startswith("@"):
            return partial(attribute, path="/".join(front), attr=last[1:])
        else:
            return partial(etree, path=path)


############################################################
# DATA EXTRACTION OPERATIONS
############################################################


_EMPTY: Mapping = MappingProxyType({})


StrTransformer = Callable[[str], Any]
MapTransformer = Callable[[Mapping], Any]

StrExtractor = Callable[[Element], str]
MapExtractor = Callable[[Element], Mapping]


class Extractor(ABC):
    """An abstract base extractor.

    This class handles the common extraction operations such as
    transforming obtained raw values and handling multi-valued data.
    """

    def __init__(self, transform=None, foreach=None):
        self.transform = transform
        self.iterate = xpath(foreach) if foreach is not None else None

    @abstractmethod
    def extract(self, element):
        """Extract the raw data from the element."""

    def __call__(self, element):
        """Extract the data from the element."""
        if self.iterate is None:
            raw = self.extract(element)
            if raw is _EMPTY:
                return _EMPTY
            return raw if self.transform is None else self.transform(raw)
        else:
            raw_ = [self.extract(r) for r in self.iterate(element)]
            raw = [v for v in raw_ if v is not _EMPTY]
            if len(raw) == 0:
                return _EMPTY
            return raw if self.transform is None else \
                [self.transform(v) for v in raw]


class Path(Extractor):
    """An extractor that can get a single piece of data from an element.

    :param path: XPath expression for getting the raw data values.
    :param sep: Separator for joining the raw data values.
    :param transform: Function for transforming the raw data.
    :param foreach: XPath expression for selecting multiple subelements.
    """

    def __init__(self, path: str, *, sep: str = "",
                 transform: Union[StrTransformer, None] = None,
                 foreach: Union[str, None] = None) -> None:
        super().__init__(transform=transform, foreach=foreach)
        self.xpath = xpath(path)
        self.sep = sep

    def extract(self, element):
        selected = self.xpath(element)
        return self.sep.join(selected) if len(selected) > 0 else _EMPTY


class Items(Extractor):
    """An extractor that can get multiple pieces of data from an element.

    :param rules: Functions for generating the items from the element.
    :param section: XPath expression for selecting the root element.
    :param transform: Function for transforming the raw data items.
    :param foreach: XPath expression for selecting multiple subelements.
    """

    def __init__(self, rules: Sequence[MapExtractor], *,
                 section: Union[str, None] = None,
                 transform: Union[MapTransformer, None] = None,
                 foreach: Union[str, None] = None) -> None:
        super().__init__(transform=transform, foreach=foreach)
        self.rules = rules
        self.sections = xpath(section) if section is not None else None

    def extract(self, element):
        if self.sections is None:
            subroot = element
        else:
            subroots = self.sections(element)
            if len(subroots) == 0:
                return _EMPTY
            if len(subroots) > 1:
                raise ValueError("Section path must select a single element")
            subroot = subroots[0]

        data = {}
        for rule in self.rules:
            item = rule(subroot)
            data.update(item)
        return data if len(data) > 0 else _EMPTY


class Rule:
    """A data generator.

    :param key: Name to distinguish the data.
    :param value: Extractor that will generate the data.
    :param foreach: XPath expression for generating multiple data items.
    """

    def __init__(self, key: Union[str, StrExtractor], value: Extractor, *,
                 foreach: Union[str, None] = None) -> None:
        self.key = key
        self.value = value
        self.iterate = xpath(foreach) if foreach is not None else None

    def __call__(self, element):
        """Apply this rule to an element."""
        data = {}
        subroots = [element] if self.iterate is None else self.iterate(element)
        for subroot in subroots:
            key = self.key if isinstance(self.key, str) else self.key(subroot)
            if key is _EMPTY:
                continue

            value = self.value(subroot)
            if value is _EMPTY:
                continue
            data[key] = value
        return data if len(data) > 0 else _EMPTY


def extractor(desc: Union[str, MutableMapping]) -> Union[Path, Items]:
    """Create an extractor from a description."""
    if isinstance(desc, str):
        return Path(desc)

    transform_name = desc.pop("transform", None)
    if transform_name is not None:
        transform = getattr(transformers, transform_name, None)
        if transform is None:
            raise ValueError(f"Unknown transformer: '{transform_name}'")
        desc["transform"] = transform

    path = desc.pop("path", None)
    if path is not None:
        return Path(path, **desc)
    else:
        rules = [rule(**i) for i in desc.pop("items", [])]
        return Items(rules, **desc)


def rule(key, value, foreach=None):
    """Create a rule from a description."""
    key = key if isinstance(key, str) else extractor(key)
    value = extractor(value)
    return Rule(key=key, value=value, foreach=foreach)


############################################################
# PREPROCESSORS
############################################################


Preprocessor = Callable[[Element], None]


def _remove(path: str) -> Preprocessor:
    """Create a preprocessor that will remove selected elements from a tree.

    :param path: XPath expression to select the elements to remove.
    """
    applier = xpath(path)

    def apply(root):
        elements = applier(root)
        for element in elements:
            # XXX: could this be hazardous?
            #   parent removed in earlier iteration?
            parent = get_parent(element)
            parent.remove(element)

    return apply


def _set_attr(path: str, name: Union[str, StrExtractor],
              value: Union[str, StrExtractor]) -> Preprocessor:
    """Create a preprocessor that will set an attribute for selected elements.

    :param path: XPath to select the elements to set attributes for.
    :param name: Name of attribute to set.
    :param value: Value of attribute to set.
    """
    applier = xpath(path)

    def apply(root):
        elements = applier(root)
        for element in elements:
            name_ = name if isinstance(name, str) else name(element)
            if name_ is _EMPTY:
                continue

            value_ = value if isinstance(value, str) else value(element)
            if value_ is _EMPTY:
                continue

            element.set(name_, value_)

    return apply


def _set_text(path: str, text: Union[str, StrExtractor]) -> Preprocessor:
    """Create a preprocessor that will set the text for selected elements.

    :param path: XPath to select the elements to set attributes for.
    :param text: Value of text to set.
    """
    applier = xpath(path)

    def apply(root):
        elements = applier(root)
        for element in elements:
            text_ = text if isinstance(text, str) else text(element)
            # note that if the text is empty the existing text will be cleared
            element.text = text_ if text_ is not _EMPTY else None

    return apply


preprocessors = SimpleNamespace(
    remove=_remove,
    set_attr=_set_attr,
    set_text=_set_text,
)
"""Predefined preprocessors."""


def preprocessor(desc):
    """Create a preprocessor from a description."""
    op = desc["op"]
    func = getattr(preprocessors, op, None)
    if func is None:
        raise ValueError(f"Unknown preprocessing operation: '{op}'")
    args = {
        k: v if isinstance(v, str) else extractor(v)
        for k, v in desc.items()
        if k not in {"op", "path"}
    }
    return func(path=desc["path"], **args)


############################################################
# TRANSFORMERS
############################################################


_re_spaces = re.compile(r"\s+")
_re_symbols = re.compile(r"[^a-z0-9_]")


transformers = SimpleNamespace(
    int=int.__call__,
    float=float.__call__,
    bool=bool.__call__,
    len=len,
    lower=str.lower,
    upper=str.upper,
    capitalize=str.capitalize,
    lstrip=str.lstrip,
    rstrip=str.rstrip,
    strip=str.strip,
    clean=lambda s: _re_spaces.sub(" ", s.replace("\xa0", " ")).strip(),
    normalize=lambda s: _re_symbols.sub("", s.lower().replace(" ", "_")),
)
"""Predefined transformers."""


############################################################
# MAIN API
############################################################


def scrape(document: str, spec: Mapping, *, html: bool = False) -> Mapping:
    """Extract data from a document.

    :param document: Document to scrape.
    :param spec: Preprocessing and extraction specification.
    :param html: Whether to use the HTML builder.
    """
    root = build_tree(document, html=html)

    pre_ops = [preprocessor(p) for p in spec.get("pre", [])]
    for op in pre_ops:
        op(root)

    rules = [rule(**item) for item in spec.get("items", [])]
    items = Items(rules, section=spec.get("section"))
    return items(root)


############################################################
# COMMAND-LINE INTERFACE
############################################################


def main():
    parser = ArgumentParser(description="extract data from XML/HTML")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("document", nargs="?", type=pathlib.Path,
                        help="document to extract data from")
    parser.add_argument("--html", action="store_true",
                        help="document is in HTML format")
    parser.add_argument("-s", "--spec", required=True, type=pathlib.Path,
                        help="spec file")
    arguments = parser.parse_args()

    if arguments.document is not None:
        content = arguments.document.read_text()
    else:
        content = sys.stdin.read()

    spec_content = arguments.spec.read_text()
    spec = json.loads(spec_content)
    data = scrape(content, spec, html=arguments.html)
    print(json.dumps(data, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
