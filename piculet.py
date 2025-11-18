# Copyright (C) 2014-2025 H. Turgut Uyar <uyar@tekir.org>
#
# Piculet is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Piculet is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Piculet.  If not, see <http://www.gnu.org/licenses/>.

"""
Piculet is a module for extracting data from HTML, XML, and JSON documents.
For HTML and XML documents, the queries are written as XPath expressions,
and for JSON documents, the queries are written as JMESPath expressions.

The documentation is available on: https://piculet.readthedocs.io/
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Literal, Mapping, TypeAlias

import lxml.etree
import lxml.html
import typedload
from jmespath import compile as compile_jmespath
from lxml.etree import XPath as compile_xpath


deserialize = partial(typedload.load, pep563=True, basiccast=False)
serialize = typedload.dump


Node: TypeAlias = lxml.etree._Element | dict

DocType: TypeAlias = Literal["html", "xml", "json"]

_PARSERS: dict[DocType, Callable[[str], Node]] = {
    "html": lxml.html.fromstring,
    "xml": lxml.etree.fromstring,
    "json": json.loads,
}


CollectedData: TypeAlias = Mapping[str, Any]

Preprocessor: TypeAlias = Callable[[Node], Node]
Postprocessor: TypeAlias = Callable[[CollectedData], CollectedData]
Transformer: TypeAlias = Callable[[Any], Any]


class Path:
    def __init__(self, path: str) -> None:
        self.path: str = path
        self._compiled: Callable[[Node], Any] = \
            compile_xpath(path) if path.startswith(("/", "./")) else \
            compile_jmespath(path).search  # type: ignore

    def query(self, root: Node) -> Any:
        value: Any = self._compiled(root)
        if isinstance(self._compiled, lxml.etree.XPath):
            return "".join(value) if len(value) > 0 else None
        return value

    def select(self, root: Node) -> list[Node]:
        value: Any = self._compiled(root)
        if isinstance(self._compiled, lxml.etree.XPath):
            return value
        return value if value is not None else []


@dataclass(kw_only=True)
class Picker:
    path: Path
    transforms: list[str] = field(default_factory=list)
    foreach: Path | None = None

    transformers: list[Transformer] = field(default_factory=list)

    def _set_transformers(self, registry: Mapping[str, Transformer]) -> None:
        self.transformers = [registry[name] for name in self.transforms]

    def extract(self, root: Node) -> Any:
        return self.path.query(root)


@dataclass(kw_only=True)
class Collector:
    rules: list[Rule] = field(default_factory=list)
    transforms: list[str] = field(default_factory=list)
    foreach: Path | None = None

    transformers: list[Transformer] = field(default_factory=list)

    def _set_transformers(self, registry: Mapping[str, Transformer]) -> None:
        self.transformers = [registry[name] for name in self.transforms]
        for rule in self.rules:
            rule._set_transformers(registry)

    def extract(self, root: Node) -> CollectedData | None:
        data: dict[str, Any] = {}
        for rule in self.rules:
            subdata = rule.apply(root)
            if subdata is not None:
                data.update(subdata)
        return data if len(data) > 0 else None


@dataclass(kw_only=True)
class Rule:
    key: str | Picker
    extractor: Picker | Collector
    foreach: Path | None = None

    def _set_transformers(self, registry: Mapping[str, Transformer]) -> None:
        self.extractor._set_transformers(registry)
        if isinstance(self.key, Picker):
            self.key._set_transformers(registry)

    def apply(self, root: Node) -> CollectedData | None:
        data: dict[str, Any] = {}

        roots = [root] if self.foreach is None else self.foreach.select(root)
        for subroot in roots:
            if self.extractor.foreach is None:
                value = self.extractor.extract(subroot)
                if value is None:
                    continue
                for transform in self.extractor.transformers:
                    value = transform(value)
            else:
                raws = [self.extractor.extract(n)
                        for n in self.extractor.foreach.select(subroot)]
                value = [v for v in raws if v is not None]
                if len(value) == 0:
                    continue
                if len(self.extractor.transforms) > 0:
                    for i in range(len(value)):
                        for transform in self.extractor.transformers:
                            value[i] = transform(value[i])

            if isinstance(self.key, str):
                key = self.key
            else:
                key = self.key.extract(subroot)
                for key_transform in self.key.transformers:
                    key = key_transform(key)
            data[key] = value

        return data if len(data) > 0 else None


@dataclass(kw_only=True)
class Spec(Collector):
    """A scraping specification."""

    doctype: DocType
    pre: list[str] = field(default_factory=list)
    post: list[str] = field(default_factory=list)

    preprocessors: list[Preprocessor] = field(default_factory=list)
    postprocessors: list[Postprocessor] = field(default_factory=list)

    def _set_pre(self, registry: Mapping[str, Preprocessor]) -> None:
        self.preprocessors = [registry[name] for name in self.pre]

    def _set_post(self, registry: Mapping[str, Postprocessor]) -> None:
        self.postprocessors = [registry[name] for name in self.post]

    def _set_transformers(self, registry: Mapping[str, Transformer]) -> None:
        for rule in self.rules:
            rule._set_transformers(registry)


def load_spec(
        content: dict,
        *,
        transformers: Mapping[str, Transformer] | None = None,
        preprocessors: Mapping[str, Preprocessor] | None = None,
        postprocessors: Mapping[str, Postprocessor] | None = None,
) -> Spec:
    """Generate a scraping specification from the content.

    The transformer, preprocessor and postprocessor functions
    used in the specification will be looked up in the corresponding
    registry parameters.

    :param content: Specification content.
    :param transformers: Transformer registry.
    :param preprocessors: Preprocessor registry.
    :param postprocessors: Preprocessor registry.
    :return: Generated specification.
    """
    spec: Spec = deserialize(
        content,
        type_=Spec,
        strconstructed={Path},
        failonextra=True,
    )
    if preprocessors is not None:
        spec._set_pre(preprocessors)
    if postprocessors is not None:
        spec._set_post(postprocessors)
    if transformers is not None:
        spec._set_transformers(transformers)
    return spec


def build_tree(document: str, *, doctype: DocType) -> Node:
    """Convert the document to a tree.

    :param document: Document to convert.
    :param doctype: Type of document.
    :return: Root node of generated tree.
    """
    return _PARSERS[doctype](document)


def scrape(document: str | Node, spec: Spec) -> CollectedData:
    """Scrape a document using a specification.

    If the document is a string, it will be converted to a tree first.

    :param document: Document to scrape.
    :param spec: Scraping specification.
    :return: Scraped data.
    """
    root = document if not isinstance(document, str) else \
        build_tree(document, doctype=spec.doctype)
    for preprocess in spec.preprocessors:
        root = preprocess(root)
    data = spec.extract(root)
    if data is None:
        return {}
    for postprocess in spec.postprocessors:
        data = postprocess(data)
    return data
