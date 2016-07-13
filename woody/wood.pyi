from typing import List, Union

from xml.etree import ElementTree


def xpath(
        element: ElementTree.Element,
        path: str
) -> Union[List[str], List[ElementTree.Element]]: ...
