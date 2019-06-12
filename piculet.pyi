# THIS FILE IS AUTOMATICALLY GENERATED, DO NOT EDIT MANUALLY.

from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Union,
)

from abc import ABC
from html.parser import HTMLParser
from pathlib import Path as FSPath
from xml.etree.ElementTree import Element

XPather = Callable[[Element], Union[Sequence[str], Sequence[Element]]]
Reducer = Callable[[Sequence[str]], str]
PathTransformer = Callable[[str], Any]
MapTransformer = Callable[[Mapping], Any]
Transformer = Union[PathTransformer, MapTransformer]

__version__ = ...  # type: str
LXML_AVAILABLE = ...  # type: bool
_EMPTY = ...  # type: Dict
preprocessors = ...  # type: Registry
reducers = ...  # type: Registry
transformers = ...  # type: Registry
YAML_AVAILABLE = ...  # type: bool


class HTMLNormalizer(HTMLParser):
    VOID_ELEMENTS = ...  # type: ClassVar[FrozenSet[str]]
    omit_tags = ...  # type: Set[str]
    omit_attrs = ...  # type: Set[str]
    def __init__(
        self,
        *,
        omit_tags: Optional[Iterable[str]] = ...,
        omit_attrs: Optional[Iterable[str]] = ...,
    ) -> None: ...

def html_to_xhtml(
    document: str,
    *,
    omit_tags: Optional[Iterable[str]] = ...,
    omit_attrs: Optional[Iterable[str]] = ...,
) -> str: ...
def xpath(path: str) -> XPather: ...

class Extractor(ABC):
    transform = ...  # type: Optional[Transformer]
    foreach = ...  # type: Optional[XPather]
    def __init__(
        self,
        *,
        transform: Optional[Transformer] = ...,
        foreach: Optional[str] = ...,
    ) -> None: ...
    def apply(self, element: Element) -> Union[str, Mapping]: ...
    def extract(self, element: Element, *, transform: bool = ...) -> Any: ...
    @staticmethod
    def from_map(item: Mapping) -> Extractor: ...

class Path(Extractor):
    path = ...  # type: XPather
    reduce = ...  # type: Reducer
    def __init__(
        self,
        path: str,
        reduce: Optional[Reducer] = ...,
        *,
        transform: Optional[PathTransformer] = ...,
        foreach: Optional[str] = ...,
    ) -> None: ...
    def apply(self, element: Element) -> str: ...

class Rules(Extractor):
    rules = ...  # type: Sequence[Rule]
    section = ...  # type: Optional[XPather]
    def __init__(
        self,
        rules: Sequence[Rule],
        *,
        section: str = ...,
        transform: Optional[MapTransformer] = ...,
        foreach: Optional[str] = ...,
    ) -> None: ...
    def apply(self, element: Element) -> Mapping: ...

class Rule:
    key = ...  # type: Union[str, Extractor]
    extractor = ...  # type: Extractor
    foreach = ...  # type: Optional[XPather]
    def __init__(
        self,
        key: Union[str, Extractor],
        extractor: Extractor,
        *,
        foreach: Optional[str] = ...,
    ) -> None: ...
    @staticmethod
    def from_map(item: Mapping) -> Rule: ...
    def extract(self, element: Element) -> Mapping: ...

def remove_elements(root: Element, path: str) -> None: ...
def set_element_attr(
    root: Element,
    path: str,
    name: Union[str, Mapping],
    value: Union[str, Mapping],
) -> None: ...
def set_element_text(
    root: Element, path: str, text: Union[str, Mapping]
) -> None: ...
def build_tree(document: str, *, lxml_html: bool = ...) -> Element: ...

class Registry:
    def __init__(self, entries: Mapping) -> None: ...
    def get(self, item: str) -> Any: ...
    def register(self, key: str, value: Any) -> None: ...

def preprocess(root: Element, pre: Sequence[Mapping]) -> None: ...
def extract(
    element: Element, items: Sequence[Mapping], *, section: Optional[str] = ...
) -> Mapping: ...
def scrape(
    document: str, spec: Mapping, *, lxml_html: bool = ...
) -> Mapping: ...
def load_spec(path: FSPath) -> Mapping: ...
def main(argv: Optional[List[str]] = ...) -> None: ...
