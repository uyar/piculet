from typing import Any, Callable, Optional, Union
from typing import Iterable, List, Mapping, Set

from xml.etree import ElementTree


def extract(
        root: ElementTree.Element,
        items: Iterable[Mapping[str, Any]],
        pre: Optional[Mapping[str, str]] = None
) -> Mapping[str, str]: ...


def html_to_xhtml(
        content: str,
        omit_tags: Optional[Set[str]] = None,
        omit_attrs: Optional[Set[str]] = None
) -> str: ...


def retrieve(
        url: str,
        charset: Optional[str] = None,
        fallback_charset: Optional[str] = 'utf-8'
) -> str: ...


def scrape(
        spec: Mapping[str, Any],
        scraper_id: str,
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
