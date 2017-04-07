# THIS FILE IS AUTOMATICALLY GENERATED, DO NOT EDIT MANUALLY.

from typing import Any, Callable, Iterable, List, Mapping, Optional, Set, Union

from html.parser import HTMLParser
from xml.etree import ElementTree


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
            omit_tags: Set[str] = ...,
            omit_attrs: Set[str] = ...
    ) -> None: ...

def html_to_xhtml(
        document: str,
        omit_tags: Optional[Iterable[str]] = ...,
        omit_attrs: Optional[Iterable[str]] = ...
) -> str: ...

def build_tree(document: str) -> ElementTree.Element: ...

def xpath_etree(
        element: ElementTree.Element,
        path: str
) -> Union[List[str], List[ElementTree.Element]]: ...

def woodpecker(
        path: str,
        reducer: Optional[str] = ...,
        reduce: Optional[Callable[[List[str]], str]] = ...
) -> Callable[[ElementTree.Element], Optional[str]]: ...

def extract(
        root: ElementTree.Element,
        items: Iterable[Mapping[str, Any]],
        pre: Optional[Iterable[Mapping[str, Any]]] = ...
) -> Mapping[str, Any]: ...

def get_document(url: str) -> str: ...

def scrape(
        document: str,
        rules: Mapping[str, Any],
        content_format: Optional[str] = ...
) -> Mapping[str, Any]: ...

def h2x(source: str) -> None: ...

def scrape_url(
        url: str,
        spec: str,
        ruleset: str,
        content_format: Optional[str] = ...
) -> None: ...

def main(argv: Optional[List[str]] = ...) -> None: ...
