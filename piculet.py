# Copyright (C) 2014-2022 H. Turgut Uyar <uyar@tekir.org>
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
other than the standard library,
which makes it very easy to integrate into applications.

For more information, please refer to the documentation:
https://tekir.org/piculet/
"""


__version__ = "2.0.0a2"


import json
import pathlib
import re
import sys
from abc import ABC, abstractmethod
from argparse import ArgumentParser
from collections import deque
from contextlib import redirect_stdout
from functools import lru_cache, partial, reduce
from html import escape as html_escape
from html.parser import HTMLParser
from io import StringIO
from itertools import dropwhile
from pkgutil import find_loader
from types import SimpleNamespace
from typing import Any, Callable, Deque, FrozenSet, Iterable, List, Mapping, Optional, Sequence, Tuple, Union


_LXML_AVAILABLE = find_loader("lxml") is not None

if _LXML_AVAILABLE:
    import lxml.etree as ElementTree
    import lxml.html
    from lxml.etree import XPath as make_xpather
else:
    from xml.etree import ElementTree


############################################################
# HTML OPERATIONS
############################################################


class HTMLNormalizer(HTMLParser):
    """HTML to XHTML converter.

    In addition to converting the document to valid XHTML,
    this will also remove unwanted tags and attributes,
    along with all comments and DOCTYPE declarations.

    :param omit_tags: Tags to remove.
    :param omit_attrs: Attributes to remove.
    """

    VOID_ELEMENTS: FrozenSet[str] = frozenset(
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
    """Tags to treat as self-closing."""

    def __init__(
        self, *, omit_tags: Iterable[str] = (), omit_attrs: Iterable[str] = ()
    ) -> None:
        super().__init__(convert_charrefs=True)
        self.omit_tags: FrozenSet[str] = frozenset(omit_tags)
        self.omit_attrs: FrozenSet[str] = frozenset(omit_attrs)

        # stacks used during normalization
        self._open_tags: Deque[str] = deque()
        self._open_omitted_tags: Deque[str] = deque()

    def handle_starttag(
        self, tag: str, attrs: List[Tuple[str, Optional[str]]]
    ) -> None:
        if tag in self.omit_tags:
            # omit starting tag
            self._open_omitted_tags.append(tag)
        if len(self._open_omitted_tags) == 0:
            # stack empty -> not in omit mode
            if "@" in tag:
                # email address in angular brackets
                print(f"&lt;{tag}&gt;", end="")
                return
            if (tag == "li") and (self._open_tags[-1] == "li"):
                # opening <li> without closing previous <li>, add </li>
                self.handle_endtag("li")
            attribs = []
            for attr_name, attr_value in attrs:
                if attr_name in self.omit_attrs:
                    # omit attribute
                    continue
                if (not attr_name[0].isalpha()) or ('"' in attr_name):
                    # malformed attribute name, ignore
                    continue
                if attr_value is None:
                    # add empty value for attribute
                    attr_value = ""
                markup = '%(name)s="%(value)s"' % {
                    "name": attr_name,
                    "value": html_escape(attr_value, quote=True),
                }
                attribs.append(markup)
            line = "<%(tag)s%(attrs)s%(slash)s>" % {
                "tag": tag,
                "attrs": (" " + " ".join(attribs)) if len(attribs) > 0 else "",
                "slash": "/" if tag in HTMLNormalizer.VOID_ELEMENTS else "",
            }
            print(line, end="")
            if tag not in HTMLNormalizer.VOID_ELEMENTS:
                self._open_tags.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if len(self._open_omitted_tags) == 0:
            # stack empty -> not in omit mode
            if tag not in HTMLNormalizer.VOID_ELEMENTS:
                last = self._open_tags[-1]
                if (tag == "ul") and (last == "li"):
                    # closing <ul> without closing last <li>, add </li>
                    self.handle_endtag("li")
                if tag == last:
                    # expected end tag
                    print(f"</{tag}>", end="")
                    self._open_tags.pop()
                elif tag not in self._open_tags:
                    # closing tag without opening tag
                    # XXX: for <a><b></a></b>, this case gets invoked after the case below
                    pass
                elif tag == self._open_tags[-2]:
                    # unexpected closing tag, close both
                    print(f"</{last}>", end="")
                    print(f"</{tag}>", end="")
                    self._open_tags.pop()
                    self._open_tags.pop()
        elif (tag in self.omit_tags) and (tag == self._open_omitted_tags[-1]):
            # end of expected omitted tag
            self._open_omitted_tags.pop()

    def handle_data(self, data: str) -> None:
        if len(self._open_omitted_tags) == 0:
            # stack empty -> not in omit mode
            print(html_escape(data), end="")

    # def feed(self, data: str) -> None:
    #     super().feed(data)
    #     # close all remaining open tags
    #     for tag in reversed(self._open_tags):
    #         print(f"</{tag}>", end='')

    def error(self, message: str) -> None:
        """Ignore errors."""


def html_to_xhtml(
    document: str, *, omit_tags: Iterable[str] = (), omit_attrs: Iterable[str] = ()
) -> str:
    """Convert an HTML document to XHTML.

    :param document: HTML document to convert.
    :param omit_tags: Tags to exclude from the output.
    :param omit_attrs: Attributes to exclude from the output.
    """
    out = StringIO()
    normalizer = HTMLNormalizer(omit_tags=omit_tags, omit_attrs=omit_attrs)
    with redirect_stdout(out):
        normalizer.feed(document)
    return out.getvalue()


############################################################
# ELEMENTTREE-LXML COMPATIBILITY
############################################################


XPathResult = Union[Sequence[str], Sequence[ElementTree.Element]]
XPather = Callable[[ElementTree.Element], XPathResult]


if _LXML_AVAILABLE:
    get_parent = ElementTree._Element.getparent
else:
    def get_parent(element: ElementTree.Element) -> ElementTree.Element:
        return element.get("__root__").get("__parents__").get(element)

    def make_xpather(path: str) -> XPather:
        """Get an XPath evaluator that can be applied to an element.

        This is needed to compensate for the lack of some features
        in ElementTree XPath support.
        """
        preps = []
        if path[0] == "/":
            # ElementTree doesn't support absolute paths
            preps.append(lambda e: e.get("__root__"))
            path = "." + path

        # ElementTree doesn't support paths starting with a parent
        if path.startswith(".."):
            path_steps = path.split("/")
            down_steps = list(dropwhile(lambda x: x == "..", path_steps))
            for _ in range(len(path_steps) - len(down_steps)):
                preps.append(get_parent)
            path = "./" + "/".join(down_steps)

        def prep(e):
            for func in preps:
                e = func(e)
            return e

        def descendant_text(element):
            # strip trailing '//text()'
            return [
                t
                for e in prep(element).findall(path[:-8])
                for t in e.itertext()
                if t
            ]

        def child_text(element):
            # strip trailing '/text()'
            return [
                t
                for e in prep(element).findall(path[:-7])
                for t in ([e.text] + [c.tail if c.tail else "" for c in e])
                if t
            ]

        def attribute(element, subpath, attr):
            result = [e.get(attr) for e in prep(element).findall(subpath)]
            return [r for r in result if r is not None]

        def regular(element):
            return prep(element).findall(path)

        if path.endswith("//text()"):
            apply = descendant_text
        elif path.endswith("/text()"):
            apply = child_text
        else:
            *front, last = path.split("/")
            if last.startswith("@"):
                apply = partial(attribute, subpath="/".join(front), attr=last[1:])
            else:
                apply = regular

        return apply


xpather: Callable[[str], XPather] = lru_cache(maxsize=None)(make_xpather)


def build_tree(document: str, *, html: bool = False) -> ElementTree.Element:
    """Build a tree from an XML document.

    :param document: XML document to build the tree from.
    :param html: Whether the document is in HTML format.
    :return: Root element of the XML tree.
    """
    if _LXML_AVAILABLE:
        if html:
            return lxml.html.fromstring(document)
        return ElementTree.fromstring(document)
    else:
        if html:
            document = html_to_xhtml(document)

        root = ElementTree.fromstring(document)

        # ElementTree doesn't support parent queries,
        # so we'll build a map for it
        parents = {e: p for p in root.iter() for e in p}
        root.set("__parents__", parents)
        root.set("__root__", root)
        for element in parents:
            element.set("__root__", root)

        return root


############################################################
# DATA EXTRACTION OPERATIONS
############################################################


_EMPTY: Mapping = {}


StrTransformer = Callable[[str], Any]
MapTransformer = Callable[[Mapping], Any]

StrExtractor = Callable[[ElementTree.Element], str]
MapExtractor = Callable[[ElementTree.Element], Mapping]


class Extractor(ABC):
    """An abstract base extractor.

    This class handles the common extraction operations such as
    transforming obtained raw values and handling multi-valued data.
    """

    def _init(self, transform=None, foreach=None):
        self.transform = transform
        self.iterate = xpather(foreach) if foreach is not None else None

    @staticmethod
    def from_desc(desc):
        """Create an extractor from a description."""
        if isinstance(desc, str):
            path, *transforms = [s.strip() for s in desc.split("|")]
            sep = None
            foreach = None
        else:
            path = desc.get("path")
            sep = desc.get("sep")
            transforms = [
                s.strip()
                for s in desc.get("transform", "").split("|")
            ]
            foreach = desc.get("foreach")
        transforms = [s for s in transforms if len(s) > 0]

        if len(transforms) == 0:
            transform = None
        else:
            ops = []
            for op_name in transforms:
                op = getattr(transformers, op_name, None)
                if op is None:
                    raise ValueError(f"Unknown transformer: '{op_name}'")
                ops.append(op)
            transform = chain(*ops)

        if path is not None:
            extractor = Path(
                path=path,
                sep=sep,
                transform=transform,
                foreach=foreach,
            )
        else:
            extractor = Items(
                rules=[Rule.from_desc(i) for i in desc.get("items", [])],
                section=desc.get("section"),
                transform=transform,
                foreach=foreach,
            )
        return extractor

    @abstractmethod
    def _raw(self, element):
        """Get the raw data from the element."""

    def __call__(self, element):
        """Extract the data from the element."""
        if self.iterate is None:
            raw = self._raw(element)
            if raw is _EMPTY:
                return _EMPTY
            return raw if self.transform is None else self.transform(raw)
        else:
            raw_ = [self._raw(r) for r in self.iterate(element)]
            raw = [v for v in raw_ if v is not _EMPTY]
            if len(raw) == 0:
                return _EMPTY
            return raw if self.transform is None else [
                self.transform(v) for v in raw
            ]


class Path(Extractor):
    """An extractor that can get a single piece of data from an element.

    :param path: XPath expression for getting the raw data values.
    :param sep: Separator for joining the raw data values.
    :param transform: Function for transforming the raw data.
    :param foreach: XPath expression for selecting multiple subelements.
    """

    def __init__(
        self,
        path: str,
        *,
        sep: Optional[str] = None,
        transform: Optional[StrTransformer] = None,
        foreach: Optional[str] = None
    ) -> None:
        super()._init(transform=transform, foreach=foreach)
        self.xpath = xpather(path)
        self.sep = sep if sep is not None else ""

    def _raw(self, element):
        selected = self.xpath(element)
        return self.sep.join(selected) if len(selected) > 0 else _EMPTY


class Items(Extractor):
    """An extractor that can get multiple pieces of data from an element.

    :param rules: Functions for generating the items from the element.
    :param section: XPath expression for selecting the root element for queries.
    :param transform: Function for transforming the raw data items.
    :param foreach: XPath expression for selecting multiple subelements.
    """

    def __init__(
        self,
        rules: Sequence[MapExtractor],
        *,
        section: Optional[str] = None,
        transform: Optional[MapTransformer] = None,
        foreach: Optional[str] = None
    ) -> None:
        super()._init(transform=transform, foreach=foreach)
        self.rules = rules
        self.sections = xpather(section) if section is not None else None

    def _raw(self, element):
        if self.sections is None:
            subroot = element
        else:
            subroots = self.sections(element)
            if len(subroots) == 0:
                return _EMPTY
            if len(subroots) > 1:
                raise ValueError("Section path must select exactly one element")
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

    def __init__(
        self,
        key: Union[str, StrExtractor],
        value: Extractor,
        *,
        foreach: Optional[str] = None
    ) -> None:
        self.key = key
        self.value = value
        self.iterate = xpather(foreach) if foreach is not None else None

    @staticmethod
    def from_desc(desc):
        """Create a rule from a description."""
        key_ = desc["key"]
        key = key_ if isinstance(key_, str) else Extractor.from_desc(key_)
        value = Extractor.from_desc(desc["value"])
        return Rule(key=key, value=value, foreach=desc.get("foreach"))

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


############################################################
# PREPROCESSORS
############################################################


Preprocessor = Callable[[ElementTree.Element], None]


def _remove(path: str) -> Preprocessor:
    """Create a preprocessor that will remove selected elements from a tree.

    :param path: XPath expression to select the elements to remove.
    """
    applier = xpather(path)

    def apply(root):
        elements = applier(root)
        if len(elements) > 0:
            for element in elements:
                # XXX: could this be hazardous? parent removed in earlier iteration?
                get_parent(element).remove(element)

    return apply


def _set_attr(
    path: str, name: Union[str, StrExtractor], value: Union[str, StrExtractor]
) -> Preprocessor:
    """Create a preprocessor that will set an attribute for selected elements.

    :param path: XPath to select the elements to set attributes for.
    :param name: Name of attribute to set.
    :param value: Value of attribute to set.
    """
    applier = xpather(path)

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
    applier = xpather(path)

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
        k: v if isinstance(v, str) else Extractor.from_desc(v)
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


def chain(*functions):
    """Chain functions to apply the output of one as the input of the next."""
    return reduce(lambda f, g: lambda x: g(f(x)), functions)


############################################################
# MAIN API
############################################################


def scrape(document: str, spec: Mapping, *, html: bool = False) -> Mapping:
    """Extract data from a document.

    :param document: Document to scrape.
    :param spec: Preprocessing and extraction specification.
    :param html: Whether to use the HTML builder.
    """
    pre_ = spec.get("pre")
    pre = [preprocessor(p) for p in pre_] if pre_ is not None else []

    items_ = spec.get("items", [])
    section = spec.get("section")
    rules = Items(
        rules=[Rule.from_desc(item) for item in items_],
        section=section,
    )

    root = build_tree(document, html=html)
    for preprocess in pre:
        preprocess(root)
    data = rules(root)
    return data


############################################################
# COMMAND-LINE INTERFACE
############################################################


def _load_spec(filepath: pathlib.Path) -> Mapping:
    if filepath.suffix in {".yaml", ".yml"}:
        if find_loader("strictyaml") is None:
            raise RuntimeError("YAML support not available")
        import strictyaml

        spec_loader = lambda s: strictyaml.load(s).data
    else:
        spec_loader = json.loads

    spec_content = filepath.read_text()
    return spec_loader(spec_content)


def main():
    parser = ArgumentParser(description="extract data from XML/HTML")
    parser.add_argument(
        "--version", action="version", version=f"{__version__}"
    )
    parser.add_argument(
        "--html", action="store_true", help="document is in HTML format"
    )

    command = parser.add_mutually_exclusive_group(required=True)
    command.add_argument(
        "-s", "--spec", help="spec file"
    )
    command.add_argument(
        "--h2x", action="store_true", help="convert HTML to XHTML"
    )

    arguments = parser.parse_args()

    content = sys.stdin.read()
    if arguments.h2x:
        print(html_to_xhtml(content), end="")
    else:
        spec = _load_spec(pathlib.Path(arguments.spec))
        data = scrape(content, spec, html=arguments.html)
        print(json.dumps(data, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
