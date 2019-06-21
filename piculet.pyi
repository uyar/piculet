# THIS FILE IS AUTOMATICALLY GENERATED, DO NOT EDIT MANUALLY.

from typing import (
    Any,
    Callable,
    ClassVar,
    FrozenSet,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from html.parser import HTMLParser
from types import SimpleNamespace
from xml.etree import ElementTree

XPather = Callable[[ElementTree.Element], Union[Sequence[str], Sequence[ElementTree.Element]]]
Reducer = Callable[[Sequence[str]], str]
StrExtractor = Callable[[ElementTree.Element], str]
MapExtractor = Callable[[ElementTree.Element], Mapping]
StrTransformer = Callable[[str], Any]
MapTransformer = Callable[[Mapping], Any]
Transformer = Union[StrTransformer, MapTransformer]
Extractor = Callable[[ElementTree.Element], Any]
Preprocessor = Callable[[ElementTree.Element], None]

__version__ = ...  # type: str
preprocessors = ...  # type: SimpleNamespace
reducers = ...  # type: SimpleNamespace
transformers = ...  # type: SimpleNamespace


class HTMLNormalizer(HTMLParser):
    VOID_ELEMENTS = ...  # type: ClassVar[FrozenSet[str]]
    omit_tags = ...  # type: FrozenSet[str]
    omit_attrs = ...  # type: FrozenSet[str]
    def __init__(
        self, *, omit_tags: Iterable[str] = ..., omit_attrs: Iterable[str] = ...
    ) -> None: ...

def html_to_xhtml(
    document: str,
    *,
    omit_tags: Iterable[str] = ...,
    omit_attrs: Iterable[str] = ...,
) -> str: ...
def build_tree(
    document: str, *, lxml_html: bool = ...
) -> ElementTree.Element: ...
def get_parent(element: ElementTree.Element) -> ElementTree.Element: ...
def make_xpather(path: str) -> XPather: ...
def make_path(
    path: str,
    reduce: Optional[Reducer] = ...,
    transform: Optional[StrTransformer] = ...,
    foreach: Optional[str] = ...,
) -> Extractor: ...
def make_items(
    rules: Sequence[MapExtractor],
    section: Optional[str] = ...,
    transform: Optional[MapTransformer] = ...,
    foreach: Optional[str] = ...,
) -> Extractor: ...
def make_rule(
    key: Union[str, StrExtractor],
    value: Extractor,
    *,
    foreach: Optional[str] = ...,
) -> MapExtractor: ...
def preprocess_remove(root: ElementTree.Element, *, path: str) -> None: ...
def preprocess_set_attr(
    root: ElementTree.Element,
    *,
    path: str,
    name: Union[str, StrExtractor],
    value: Union[str, StrExtractor],
) -> None: ...
def preprocess_set_text(
    root: ElementTree.Element, *, path: str, text: Union[str, StrExtractor]
) -> None: ...
def load_spec(filepath: str) -> Mapping: ...
def parse_spec(spec: Mapping) -> Tuple[Sequence[Preprocessor], Extractor]: ...
def scrape(
    document: str, spec: Mapping, *, lxml_html: bool = ...
) -> Mapping: ...
def main(argv: Optional[List[str]] = ...) -> None: ...
