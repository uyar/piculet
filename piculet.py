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
from argparse import ArgumentParser
from collections import deque
from contextlib import redirect_stdout
from functools import lru_cache, partial
from html import escape as html_escape
from html.parser import HTMLParser
from io import StringIO
from itertools import dropwhile
from operator import itemgetter
from pathlib import Path
from pkgutil import find_loader
from types import SimpleNamespace


__version__ = "2.0.0.dev3"  # sig: str


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

    def __init__(self, *, omit_tags=(), omit_attrs=()):
        """Initialize this normalizer.

        :sig: (Iterable[str], Iterable[str]) -> None
        :param omit_tags: Tags to remove.
        :param omit_attrs: Attributes to remove.
        """
        super().__init__(convert_charrefs=True)

        self.omit_tags = frozenset(omit_tags)  # sig: FrozenSet[str]
        self.omit_attrs = frozenset(omit_attrs)  # sig: FrozenSet[str]

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


def html_to_xhtml(document, *, omit_tags=(), omit_attrs=()):
    """Convert an HTML document to XHTML.

    :sig: (str, Iterable[str], Iterable[str]) -> str
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
# ELEMENTTREE-LXML COMPATIBILITY
###########################################################


# sigalias: XPather = Callable[[ElementTree.Element], Union[Sequence[str], Sequence[ElementTree.Element]]]


if find_loader("lxml") is not None:
    from lxml import etree
    from lxml.etree import XPath as make_xpather

    def build_tree(document, *, lxml_html=False):
        if lxml_html:
            import lxml.html

            return lxml.html.fromstring(document)
        return etree.fromstring(document)

    get_parent = etree._Element.getparent


else:
    from xml.etree import ElementTree

    def build_tree(document, *, lxml_html=False):
        """Build a tree from an XML document.

        :sig: (str, bool) -> ElementTree.Element
        :param document: XML document to build the tree from.
        :param lxml_html: Whether to use the lxml.html builder.
        :return: Root element of the XML tree.
        """
        if lxml_html:
            raise RuntimeError("LXML not available")

        root = ElementTree.fromstring(document)

        # ElementTree doesn't support parent queries, so we'll build a map for it
        parents = {e: p for p in root.iter() for e in p}
        root.set("__parents__", parents)
        root.set("__root__", root)
        for element in parents:
            element.set("__root__", root)

        return root

    def get_parent(element):
        """Get the parent node of an element.

        :sig: (ElementTree.Element) -> ElementTree.Element
        :param element: Element for which to find the parent.
        :return: Parent of element.
        """
        return element.get("__root__").get("__parents__").get(element)

    def make_xpather(path):
        """Get an XPath evaluator that can be applied to an element.

        This is needed to compensate for the lack of some features
        in ElementTree XPath support.

        :sig: (str) -> XPather
        :param path: XPath expression to apply.
        :return: Evaluator that applies the expression to an element.
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
            return [t for e in prep(element).findall(path[:-8]) for t in e.itertext() if t]

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


make_xpather = lru_cache(maxsize=None)(make_xpather)


###########################################################
# DATA EXTRACTION OPERATIONS
###########################################################


_EMPTY = {}


# sigalias: Reducer = Callable[[Sequence[str]], str]

# sigalias: StrExtractor = Callable[[ElementTree.Element], str]
# sigalias: MapExtractor = Callable[[ElementTree.Element], Mapping]

# sigalias: StrTransformer = Callable[[str], Any]
# sigalias: MapTransformer = Callable[[Mapping], Any]
# sigalias: Transformer = Union[StrTransformer, MapTransformer]

# sigalias: Extractor = Callable[[ElementTree.Element], Any]


def _make_extractor(raw, transform=None, foreach=None):
    iterate = make_xpather(foreach) if foreach is not None else None

    def apply(element):
        if iterate is None:
            raw_value = raw(element)
            if raw_value is _EMPTY:
                return raw_value
            return raw_value if transform is None else transform(raw_value)
        else:
            raw_values = [raw(r) for r in iterate(element)]
            raw_values = [v for v in raw_values if v is not _EMPTY]
            if len(raw_values) == 0:
                return _EMPTY
            return raw_values if transform is None else list(map(transform, raw_values))

    return apply


def make_path(path, reduce=None, transform=None, foreach=None):
    """Create an extractor that can get a single piece of data from an element.

    :sig:
        (
            str,
            Optional[Reducer],
            Optional[StrTransformer],
            Optional[str]
        ) -> Extractor
    :param path: XPath expression for getting the raw data values.
    :param reduce: Function for reducing the raw data values to a single value.
    :param transform: Function for transforming the reduced value.
    :param foreach: XPath expression for selecting multiple subelements to extract data from.
    :return: Function to apply to an element to extract the data as specified.
    """
    xpath = make_xpather(path)
    reduce = reducers.concat if reduce is None else reduce

    def get_raw(element):
        selected = xpath(element)
        return reduce(selected) if len(selected) > 0 else _EMPTY

    return _make_extractor(get_raw, transform=transform, foreach=foreach)


def make_items(rules, section=None, transform=None, foreach=None):
    """Create an extractor that can get multiple pieces of data from an element.

    :sig:
        (
            Sequence[MapExtractor],
            Optional[str],
            Optional[MapTransformer],
            Optional[str]
        ) -> Extractor
    :param rules: Functions for generating the items from the element.
    :param section: XPath expression for selecting the root element for queries.
    :param transform: Function for transforming the extracted data items.
    :param foreach: XPath expression for selecting multiple subelements to extract data from.
    :return: Function to apply to an element to extract the data as specified.
    """
    sections = make_xpather(section) if section is not None else None

    def get_raw(element):
        if sections is None:
            subroot = element
        else:
            subroots = sections(element)
            if len(subroots) == 0:
                return _EMPTY
            if len(subroots) > 1:
                raise ValueError("Section path should select exactly one element")
            subroot = subroots[0]

        data = {}
        for rule in rules:
            item = rule(subroot)
            data.update(item)
        return data if len(data) > 0 else _EMPTY

    return _make_extractor(get_raw, transform=transform, foreach=foreach)


def make_rule(key, value, *, foreach=None):
    """Create a data generator that can be applied to an element.

    :sig: (Union[str, StrExtractor], Extractor, Optional[str]) -> MapExtractor
    :param key: Name to distinguish the data.
    :param value: Extractor that will generate the data.
    :param foreach: XPath expression for generating multiple data items.
    :return: Function to apply to an element to generate the data as specified.
    """
    iterate = make_xpather(foreach) if foreach is not None else None

    def apply(element):
        data = {}
        subroots = [element] if iterate is None else iterate(element)
        for subroot in subroots:
            key_ = key if isinstance(key, str) else key(subroot)
            if key_ is _EMPTY:
                continue

            value_ = value(subroot)
            if value_ is _EMPTY:
                continue
            data[key_] = value_
        return data if len(data) > 0 else _EMPTY

    return apply


###########################################################
# PREPROCESSING OPERATIONS
###########################################################


def preprocess_remove(root, *, path):
    """Remove selected elements from the tree.

    :sig: (ElementTree.Element, str) -> None
    :param root: Root element of the tree.
    :param path: XPath expression to select the elements to remove.
    """
    elements = make_xpather(path)(root)
    if len(elements) > 0:
        for element in elements:
            # XXX: could this be hazardous? parent removed in earlier iteration?
            get_parent(element).remove(element)


def preprocess_set_attr(root, *, path, name, value):
    """Set an attribute for selected elements.

    :sig:
        (
            ElementTree.Element,
            str,
            Union[str, StrExtractor],
            Union[str, StrExtractor]
        ) -> None
    :param root: Root element of the tree.
    :param path: XPath to select the elements to set attributes for.
    :param name: Name of attribute to set.
    :param value: Value of attribute to set.
    """
    elements = make_xpather(path)(root)
    for element in elements:
        name_ = name if isinstance(name, str) else name(element)
        if name_ is _EMPTY:
            continue

        value_ = value if isinstance(value, str) else value(element)
        if value_ is _EMPTY:
            continue

        element.set(name_, value_)


def preprocess_set_text(root, *, path, text):
    """Set the text for selected elements.

    :sig: (ElementTree.Element, str, Union[str, StrExtractor]) -> None
    :param root: Root element of the tree.
    :param path: XPath to select the elements to set attributes for.
    :param text: Value of text to set.
    """
    elements = make_xpather(path)(root)
    for element in elements:
        text_ = text if isinstance(text, str) else text(element)
        # note that the text can be empty in which case the existing text will be cleared
        element.text = text_ if text_ is not _EMPTY else None


###########################################################
# PREDEFINED HELPERS
###########################################################


preprocessors = SimpleNamespace(  # sig: SimpleNamespace
    remove=lambda **kwargs: partial(preprocess_remove, **kwargs),
    set_attr=lambda **kwargs: partial(preprocess_set_attr, **kwargs),
    set_text=lambda **kwargs: partial(preprocess_set_text, **kwargs),
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
# SPECIFICATION DESCRIPTION OPERATIONS
###########################################################


def _make_extractor_from_desc(desc):
    transform = desc.get("transform")
    if transform is None:
        transform_ = None
    else:
        transform_ = getattr(transformers, transform, None)
        if transform_ is None:
            raise ValueError("Unknown transformer")

    foreach = desc.get("foreach")

    path = desc.get("path")
    if path is not None:
        reduce = desc.get("reduce")
        if reduce is None:
            reduce_ = None
        else:
            reduce_ = getattr(reducers, reduce, None)
            if reduce_ is None:
                raise ValueError("Unknown reducer")
        extractor = make_path(path=path, reduce=reduce_, transform=transform_, foreach=foreach)
    else:
        items = desc.get("items", [])
        rules = [_make_rule_from_desc(i) for i in items]
        extractor = make_items(
            rules=rules, section=desc.get("section"), transform=transform_, foreach=foreach
        )

    return extractor


def _make_rule_from_desc(desc):
    key = desc["key"]
    key_ = key if isinstance(key, str) else _make_extractor_from_desc(key)
    value_ = _make_extractor_from_desc(desc["value"])
    return make_rule(key=key_, value=value_, foreach=desc.get("foreach"))


def _make_preprocessor_from_desc(desc):
    preprocessor = getattr(preprocessors, desc["op"], None)
    if preprocessor is None:
        raise ValueError("Unknown preprocessing operation")
    args = {
        k: v if isinstance(v, str) else _make_extractor_from_desc(v)
        for k, v in desc.items()
        if k not in {"op", "path"}
    }
    return preprocessor(path=desc["path"], **args)


###########################################################
# MAIN API
###########################################################


def scrape(document, spec, *, lxml_html=False):
    """Extract data from a document after optionally preprocessing it.

    :sig: (str, Mapping, bool) -> Mapping
    :param document: Document to scrape.
    :param spec: Extraction specification.
    :param lxml_html: Whether to use the lxml.html builder.
    :return: Extracted data.
    """
    root = build_tree(document, lxml_html=lxml_html)

    pre = spec.get("pre")
    if pre is not None:
        steps = [_make_preprocessor_from_desc(step) for step in pre]
        for preprocess in steps:
            preprocess(root)

    items = spec.get("items", [])
    section = spec.get("section")
    rules = make_items(rules=[_make_rule_from_desc(item) for item in items], section=section)
    data = rules(root)

    return data


###########################################################
# COMMAND-LINE INTERFACE
###########################################################


def load_spec(filepath):
    """Load an extraction specification from a file.

    :sig: (str) -> Mapping
    :param filepath: Path of specification file.
    :return: Loaded specification.
    """
    path = Path(filepath)
    if path.suffix in {".yaml", ".yml"}:
        if find_loader("strictyaml") is None:
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
            spec = load_spec(arguments.spec)
            if arguments.html:
                content = html_to_xhtml(content)
            data = scrape(content, spec)
            print(json.dumps(data, indent=2, sort_keys=True))
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
