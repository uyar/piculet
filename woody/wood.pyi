from typing import Iterable, List, Mapping, Optional, Union

from xml.etree import ElementTree
from woody.wood import Rule


def peck(
        element: ElementTree.Element,
        rule: Rule
) -> Optional[str]: ...


def extract(
        content: str,
        rules: Iterable[Rule],
        prune: Optional[str] = None
) -> Mapping[str, str]: ...


def xpath(
        element: ElementTree.Element,
        path: str
) -> Union[List[str], List[ElementTree.Element]]: ...
