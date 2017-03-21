# THIS FILE IS AUTOMATICALLY GENERATED, DO NOT EDIT MANUALLY.

from typing import Any, Callable, Iterable, List, Mapping, Optional, Union

from html.parser import HTMLParser

import xml.etree.ElementTree


def retrieve(
        url: str,
        charset: Optional[str] = ...,
        fallback_charset: Optional[str] = ...
) -> str: ...

class _HTMLNormalizer(HTMLParser): ...

def html_to_xhtml(
        document: str,
        omit_tags: Optional[Iterable[str]] = ...,
        omit_attrs: Optional[Iterable[str]] = ...
) -> str: ...

def xpath_etree(
        element: xml.etree.ElementTree.Element,
        path: str
) -> Union[List[str], List[xml.etree.ElementTree.Element]]: ...

def woodpecker(
        path: str,
        reducer: str
) -> Callable[[xml.etree.ElementTree.Element], Optional[str]]: ...

def extract(
        document: Union[str, xml.etree.ElementTree.Element],
        items: Iterable[Mapping[str, Any]],
        pre: Optional[Iterable[Mapping[str, Any]]] = ...
) -> Mapping[str, Any]: ...

def scrape(
        url: str,
        spec: Mapping[str, Any],
        scraper: str,
        content_format: Optional[str] = ...
) -> Mapping[str, Any]: ...
