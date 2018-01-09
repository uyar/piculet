# THIS FILE IS AUTOMATICALLY GENERATED, DO NOT EDIT MANUALLY.

from typing import Any, Callable, Iterable, List, Mapping, Optional, Sequence, Set, Union

from html.parser import HTMLParser
from xml.etree import ElementTree


class SimpleNamespace: ...

def decode_html(
        content: bytes,
        charset: Optional[str] = ...,
        fallback_charset: Optional[str] = ...
) -> str: ...

class HTMLNormalizer(HTMLParser):
    omit_tags = ...   # type: Set[str]
    omit_attrs = ...  # type: Set[str]

    def __init__(
            self,
            omit_tags: Optional[Iterable[str]] = ...,
            omit_attrs: Optional[Iterable[str]] = ...
    ) -> None: ...

def html_to_xhtml(
        document: str,
        omit_tags: Optional[Iterable[str]] = ...,
        omit_attrs: Optional[Iterable[str]] = ...
) -> str: ...

def build_tree(
        document: str,
        force_html: Optional[bool] = ...
) -> ElementTree.Element: ...

def xpath_etree(
        element: ElementTree.Element,
        path: str
) -> Union[Sequence[str], Sequence[ElementTree.Element]]: ...

class Extractor:
    transform = ...  # type: Optional[Callable[[str], Any]]
    foreach = ...    # type: Optional[str]

    def __init__(
            self,
            transform: Optional[Callable[[Union[str, Mapping[str, Any]]], Any]] = ...,
            foreach: Optional[str] = ...
    ) -> None: ...

    def apply(
            self,
            element: ElementTree.Element
    ) -> Union[str, Mapping[str, Any]]: ...

    def extract(
            self,
            element: ElementTree.Element,
            transform: Optional[bool] = ...
    ) -> Any: ...

    @staticmethod
    def from_map(item: Mapping[str, Any]) -> Extractor: ...

class Path(Extractor):
    path = ...    # type: str
    reduce = ...  # type: Callable[[Sequence[str]], str]

    def __init__(
            self,
            path: str,
            reduce: Optional[Callable[[Sequence[str]], str]] = ...,
            transform: Optional[Callable[[str], Any]] = ...,
            foreach: Optional[str] = ...
    ) -> None: ...

    def apply(self, element: ElementTree.Element) -> str: ...

class Rules(Extractor):
    subrules = ...  # type: Iterable[Rule]

    def __init__(
            self,
            subrules: Iterable[Rule],
            transform: Optional[Callable[[Mapping[str, Any]], Any]] = ...,
            foreach: Optional[str] = ...
    ) -> None: ...

    def apply(self, element: ElementTree.Element) -> Mapping[str, Any]: ...

class Rule:
    key = ...        # type: Union[str, Extractor]
    extractor = ...  # type: Extractor
    section = ...    # type: Optional[str]

    def __init__(
            self,
            key: Union[str, Extractor],
            extractor: Extractor,
            section: Optional[str] = ...
    ) -> None: ...

    @staticmethod
    def from_map(item: Mapping[str, Any]) -> Rule: ...

    def extract(self, element: ElementTree.Element) -> Mapping[str, Any]: ...

def extract(
        element: ElementTree.Element,
        items: Iterable[Mapping[str, Any]]
) -> Mapping[str, Any]: ...

def set_root_node(
        root: ElementTree.Element,
        path: str
) -> ElementTree.Element: ...

def remove_nodes(
        root: ElementTree.Element,
        path: str
) -> ElementTree.Element: ...

def set_node_attr(
        root: ElementTree.Element,
        path: str,
        name: Union[str, Mapping[str, Any]],
        value: Union[str, Mapping[str, Any]]
) -> ElementTree.Element: ...

def set_node_text(
        root: ElementTree.Element,
        path: str,
        text: Union[str, Mapping[str, Any]]
) -> ElementTree.Element: ...

def preprocess(
        root: ElementTree.Element,
        pre: Iterable[Mapping[str, Any]]
) -> ElementTree.Element: ...

def scrape(
        document: str,
        rules: Mapping[str, Any],
        content_format: Optional[str] = ...
) -> Mapping[str, Any]: ...

def h2x(source: str) -> None: ...

def scrape_document(
        address: str,
        spec: str,
        content_format: Optional[str] = ...
) -> None: ...

def main(argv: Optional[List[str]] = ...) -> None: ...
