from typing import List, Optional, Union

from xml.etree import ElementTree
from woody.wood import Rule


def peck(
        element: ElementTree.Element,
        rule: Rule
) -> Optional[str]: ...


def xpath(
        element: ElementTree.Element,
        path: str
) -> Union[List[str], List[ElementTree.Element]]: ...
