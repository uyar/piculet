from typing import Any, Callable, Optional, Union
from typing import Iterable, List, Mapping, Set

from argparse import ArgumentParser
from xml.etree import ElementTree


def _get_document(url: str) -> str: ...


def _get_parser() -> ArgumentParser: ...


def extract(
        content: str,
        rules: Iterable[Mapping[str, Any]],
        prune: Optional[str] = None
) -> Mapping[str, str]: ...


def html_to_xhtml(
        content: str,
        omit_tags: Optional[Set[str]] = None,
        omit_attrs: Optional[Set[str]] = None
) -> str: ...


def main() -> None: ...


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
