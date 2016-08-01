from typing import Any, Iterable, List, Mapping, Optional, Union

from xml.etree import ElementTree


XPath = str


class WoodPecker:
    def __init__(
            key: Union[str, XPath],
            path: XPath,
            reducer: str,
            foreach: Optional[XPath] = None
    ) -> None: ...

    def peck(element: ElementTree.Element) -> Optional[str]: ...


def extract(
        content: str,
        rules: Iterable[Mapping[str, Any]],
        prune: Optional[str] = None
) -> Mapping[str, str]: ...


def xpath(
        element: ElementTree.Element,
        path: str
) -> Union[List[str], List[ElementTree.Element]]: ...
