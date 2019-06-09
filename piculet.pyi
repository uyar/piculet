# THIS FILE IS AUTOMATICALLY GENERATED, DO NOT EDIT MANUALLY.

from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Union,
)

from argparse import ArgumentParser
from html.parser import HTMLParser
from xml.etree.ElementTree import Element

XPathResult = Union[Sequence[str], Sequence[Element]]
Reducer = Callable[[Sequence[str]], str]
PathTransformer = Callable[[str], Any]
MapTransformer = Callable[[Mapping[str, Any]], Any]
Transformer = Union[PathTransformer, MapTransformer]
ExtractedItem = Union[str, Mapping[str, Any]]

USE_LXML = ...  # type: bool
_EMPTY = ...  # type: Dict
preprocessors = ...  # type: Registry
reducers = ...  # type: Registry
transformers = ...  # type: Registry


class HTMLNormalizer(HTMLParser):
    omit_tags = ...  # type: Set[str]
    omit_attrs = ...  # type: Set[str]
    def __init__(
        self,
        *,
        omit_tags: Optional[Iterable[str]] = ...,
        omit_attrs: Optional[Iterable[str]] = ...,
    ) -> None: ...

def html_to_xhtml(
    document: str,
    *,
    omit_tags: Optional[Iterable[str]] = ...,
    omit_attrs: Optional[Iterable[str]] = ...,
) -> str: ...

class XPath:
    _apply = ...  # type: Callable[[Element], XPathResult]
    def __init__(self, path: str) -> None: ...
    def __call__(self, element: Element) -> XPathResult: ...

def xpath(path: str) -> XPath: ...

class Extractor:
    transform = ...  # type: Optional[Transformer]
    foreach = ...  # type: Optional[XPath]
    def __init__(
        self,
        *,
        transform: Optional[Transformer] = ...,
        foreach: Optional[str] = ...,
    ) -> None: ...
    def apply(self, element: Element) -> ExtractedItem: ...
    def extract(self, element: Element, *, transform: bool = ...) -> Any: ...
    @staticmethod
    def from_map(item: Mapping[str, Any]) -> Extractor: ...

class Path(Extractor):
    path = ...  # type: XPath
    reduce = ...  # type: Reducer
    def __init__(
        self,
        path: str,
        reduce: Optional[Reducer] = ...,
        *,
        transform: Optional[PathTransformer] = ...,
        foreach: Optional[str] = ...,
    ) -> None: ...
    def apply(self, element: Element) -> str: ...

class Rules(Extractor):
    rules = ...  # type: Sequence[Rule]
    section = ...  # type: Optional[XPath]
    def __init__(
        self,
        rules: Sequence[Rule],
        *,
        section: str = ...,
        transform: Optional[MapTransformer] = ...,
        foreach: Optional[str] = ...,
    ) -> None: ...
    def apply(self, element: Element) -> Mapping[str, Any]: ...

class Rule:
    key = ...  # type: Union[str, Extractor]
    extractor = ...  # type: Extractor
    foreach = ...  # type: Optional[XPath]
    def __init__(
        self,
        key: Union[str, Extractor],
        extractor: Extractor,
        *,
        foreach: Optional[str] = ...,
    ) -> None: ...
    @staticmethod
    def from_map(item: Mapping[str, Any]) -> Rule: ...
    def extract(self, element: Element) -> Mapping[str, Any]: ...

def remove_elements(root: Element, path: str) -> None: ...
def set_element_attr(
    root: Element,
    path: str,
    name: Union[str, Mapping[str, Any]],
    value: Union[str, Mapping[str, Any]],
) -> None: ...
def set_element_text(
    root: Element, path: str, text: Union[str, Mapping[str, Any]]
) -> None: ...
def build_tree(document: str, *, lxml_html: bool = ...) -> Element: ...

class Registry:
    def __init__(self, entries: Mapping[str, Any]) -> None: ...
    def get(self, item: str) -> Any: ...
    def register(self, key: str, value: Any) -> None: ...

def preprocess(root: Element, pre: Sequence[Mapping[str, Any]]) -> None: ...
def extract(
    element: Element,
    items: Sequence[Mapping[str, Any]],
    *,
    section: Optional[str] = ...,
) -> Mapping[str, Any]: ...
def scrape(
    document: str, spec: Mapping[str, Any], *, lxml_html: bool = ...
) -> Mapping[str, Any]: ...
def h2x(source: str) -> None: ...
def scrape_document(
    address: str, spec: str, *, content_format: str = ...
) -> None: ...
def make_parser(prog: str) -> ArgumentParser: ...
def main(argv: Optional[List[str]] = ...) -> None: ...
