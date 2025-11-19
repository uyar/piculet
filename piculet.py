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


Node: TypeAlias = lxml.etree._Element | dict[str, Any]

DocType: TypeAlias = Literal["html", "xml", "json"]

_PARSERS: dict[DocType, Callable[[str], Node]] = {
    "html": lxml.html.fromstring,
    "xml": lxml.etree.fromstring,
    "json": json.loads,
}


Preprocessor: TypeAlias = Callable[[Node], Node]
Postprocessor: TypeAlias = Callable[[dict[str, Any]], dict[str, Any]]
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

    def get(self, root: Node) -> Node:
        value: Any = self._compiled(root)
        if isinstance(self._compiled, lxml.etree.XPath):
            return value[0]
        return value

    def select(self, root: Node) -> list[Node]:
        value: Any = self._compiled(root)
        if isinstance(self._compiled, lxml.etree.XPath):
            return value
        return value if value is not None else []


@dataclass(kw_only=True)
class Extractor:
    root: Path | None = None
    foreach: Path | None = None
    transforms: list[str] = field(default_factory=list)

    _transforms: list[Transformer] = field(default_factory=list)

    def _set_transforms(self, registry: Mapping[str, Transformer]) -> None:
        self._transforms = [registry[name] for name in self.transforms]


@dataclass(kw_only=True)
class Picker(Extractor):
    path: Path

    def extract(self, root: Node) -> Any:
        return self.path.query(root)


@dataclass(kw_only=True)
class Collector(Extractor):
    rules: list[Rule] = field(default_factory=list)

    def _set_transforms(self, registry: Mapping[str, Transformer]) -> None:
        super()._set_transforms(registry)
        for rule in self.rules:
            rule._set_transformers(registry)

    def extract(self, root: Node) -> dict[str, Any] | None:
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
        self.extractor._set_transforms(registry)
        if isinstance(self.key, Picker):
            self.key._set_transforms(registry)

    def apply(self, root: Node) -> dict[str, Any] | None:
        data: dict[str, Any] = {}

        if self.extractor.root is not None:
            root = self.extractor.root.get(root)
        nodes = [root] if self.foreach is None else self.foreach.select(root)
        for node in nodes:
            if self.extractor.foreach is None:
                value = self.extractor.extract(node)
                if value is None:
                    continue
                for transform in self.extractor._transforms:
                    value = transform(value)
            else:
                raws = [self.extractor.extract(n)
                        for n in self.extractor.foreach.select(node)]
                value = [v for v in raws if v is not None]
                if len(value) == 0:
                    continue
                if len(self.extractor.transforms) > 0:
                    for i in range(len(value)):
                        for transform in self.extractor._transforms:
                            value[i] = transform(value[i])

            if isinstance(self.key, str):
                key = self.key
            else:
                key = self.key.extract(node)
                for key_transform in self.key._transforms:
                    key = key_transform(key)
            data[key] = value

        return data if len(data) > 0 else None


@dataclass(kw_only=True)
class Spec(Collector):
    """A scraping specification."""

    doctype: DocType
    pre: list[str] = field(default_factory=list)
    post: list[str] = field(default_factory=list)

    _pre: list[Preprocessor] = field(default_factory=list)
    _post: list[Postprocessor] = field(default_factory=list)

    def _set_pre(self, registry: Mapping[str, Preprocessor]) -> None:
        self._pre = [registry[name] for name in self.pre]

    def _set_post(self, registry: Mapping[str, Postprocessor]) -> None:
        self._post = [registry[name] for name in self.post]

    def build_tree(self, document: str, preprocess: bool = True) -> Node:
        """Convert the document to a tree of this spec's doctype."""
        root = _PARSERS[self.doctype](document)
        if preprocess:
            root = self.preprocess(root)
        return root

    def preprocess(self, root: Node) -> Node:
        """Apply the preprocessors in this spec to the root node."""
        for preprocess in self._pre:
            root = preprocess(root)
        return root

    def extract(self, root: Node, postprocess: bool = True):
        data = super().extract(root)
        if data is None:
            return {}
        if postprocess:
            data = self.postprocess(data)
        return data

    def postprocess(self, data: dict[str, Any]) -> dict[str, Any]:
        """Apply the postprocessors in this spec to the collected data."""
        for postprocess in self._post:
            data = postprocess(data)
        return data

    def scrape(self, document: str) -> dict[str, Any]:
        """Scrape a document using this specification.

        :param document: Document to scrape.
        :return: Scraped data.
        """
        root = self.build_tree(document)
        return self.extract(root)


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
        spec._set_transforms(transformers)
    return spec
