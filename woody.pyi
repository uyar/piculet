from typing import Any, Callable, Optional, Union
from typing import Iterable, List, Mapping

from xml.etree import ElementTree


def extract(
        document: Union[str, ElementTree.Element],
        items: Iterable[Mapping[str, Any]],
        pre: Optional[Iterable[Mapping[str, Any]]] = ()
) -> Mapping[str, Any]: ...


def html_to_xhtml(
        document: str,
        omit_tags: Optional[Iterable[str]] = (),
        omit_attrs: Optional[Iterable[str]] = ()
) -> str: ...


def retrieve(
        url: str,
        charset: Optional[str] = None,
        fallback_charset: Optional[str] = 'utf-8'
) -> str: ...


def scrape(
        spec: Mapping[str, Any],
        scraper: str,
        **kwargs
) -> Mapping[str, Any]: ...


def woodpecker(
        path: str,
        reducer: str
) -> Callable[[ElementTree.Element], Optional[str]]: ...


def xpath(
        element: ElementTree.Element,
        path: str
) -> Union[List[str], List[ElementTree.Element]]: ...
