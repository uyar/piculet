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

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial
from types import MappingProxyType
from typing import Any, Literal, Mapping, TypeAlias, Union

import lxml.etree
import lxml.html
import typedload
from jmespath import compile as compile_jmespath
from lxml.etree import XPath as compile_xpath


deserialize = partial(typedload.load, pep563=True, basiccast=False)
serialize = typedload.dump


XMLNode: TypeAlias = lxml.etree._Element
JSONNode: TypeAlias = dict


DocType: TypeAlias = Literal["html", "xml", "json"]

_PARSERS: dict[DocType, Callable[[str], XMLNode | JSONNode]] = {
    "html": lxml.html.fromstring,
    "xml": lxml.etree.fromstring,
    "json": json.loads,
}


CollectedData: TypeAlias = Mapping[str, Any]

Preprocessor: TypeAlias = Callable[[XMLNode | JSONNode], XMLNode | JSONNode]
Postprocessor: TypeAlias = Callable[[CollectedData], CollectedData]
Transformer: TypeAlias = Callable[[Any], Any]

_EMPTY_REGISTRY: Mapping[str, Callable] = MappingProxyType({})


class XMLPath:
    def __init__(self, path: str) -> None:
        self.path: str = path
        self._compiled = compile_xpath(path)

    def __str__(self) -> str:
        return self.path

    def apply(self, root: XMLNode) -> str | None:
        selected: list[str] = self._compiled(root)  # type: ignore
        return "".join(selected) if len(selected) > 0 else None

    def select(self, root: XMLNode) -> list[XMLNode]:
        return self._compiled(root)  # type: ignore


class JSONPath:
    def __init__(self, path: str) -> None:
        self.path: str = path
        self._compiled = compile_jmespath(path).search

    def __str__(self) -> str:
        return self.path

    def apply(self, root: JSONNode) -> Any:
        return self._compiled(root)

    def select(self, root: JSONNode) -> list[JSONNode]:
        selected = self._compiled(root)
        return selected if selected is not None else []  # type: ignore


@dataclass(kw_only=True)
class XMLPicker:
    path: XMLPath
    transforms: list[str] = field(default_factory=list)
    foreach: XMLPath | None = None

    transformers: list[Transformer] = field(default_factory=list)

    def set_transformers(self, registry: Mapping[str, Transformer]) -> None:
        self.transformers = [registry[name] for name in self.transforms]

    def extract(self, root: XMLNode) -> Any:
        return self.path.apply(root)


@dataclass(kw_only=True)
class JSONPicker:
    path: JSONPath
    transforms: list[str] = field(default_factory=list)
    foreach: JSONPath | None = None

    transformers: list[Transformer] = field(default_factory=list)

    def set_transformers(self, registry: Mapping[str, Transformer]) -> None:
        self.transformers = [registry[name] for name in self.transforms]

    def extract(self, root: JSONNode) -> Any:
        return self.path.apply(root)


@dataclass(kw_only=True)
class XMLCollector:
    rules: list[XMLRule] = field(default_factory=list)
    transforms: list[str] = field(default_factory=list)
    foreach: XMLPath | None = None

    transformers: list[Transformer] = field(default_factory=list)

    def set_transformers(self, registry: Mapping[str, Transformer]) -> None:
        self.transformers = [registry[name] for name in self.transforms]
        for rule in self.rules:
            rule.set_transformers(registry)

    def extract(self, root: XMLNode) -> CollectedData | None:
        return collect_xml(root, self.rules)


@dataclass(kw_only=True)
class JSONCollector:
    rules: list[JSONRule] = field(default_factory=list)
    transforms: list[str] = field(default_factory=list)
    foreach: JSONPath | None = None

    transformers: list[Transformer] = field(default_factory=list)

    def set_transformers(self, registry: Mapping[str, Transformer]) -> None:
        self.transformers = [registry[name] for name in self.transforms]
        for rule in self.rules:
            rule.set_transformers(registry)

    def extract(self, root: JSONNode) -> CollectedData | None:
        return collect_json(root, self.rules)


@dataclass(kw_only=True)
class XMLRule:
    key: str | XMLPicker
    extractor: XMLPicker | XMLCollector
    transforms: list[str] = field(default_factory=list)
    foreach: XMLPath | None = None

    transformers: list[Transformer] = field(default_factory=list)

    def set_transformers(self, registry: Mapping[str, Transformer]) -> None:
        self.transformers = [registry[name] for name in self.transforms]
        self.extractor.set_transformers(registry)
        if not isinstance(self.key, str):
            self.key.set_transformers(registry)


@dataclass(kw_only=True)
class JSONRule:
    key: str | JSONPicker
    extractor: JSONPicker | JSONCollector
    transforms: list[str] = field(default_factory=list)
    foreach: JSONPath | None = None

    transformers: list[Transformer] = field(default_factory=list)

    def set_transformers(self, registry: Mapping[str, Transformer]) -> None:
        self.transformers = [registry[name] for name in self.transforms]
        self.extractor.set_transformers(registry)
        if not isinstance(self.key, str):
            self.key.set_transformers(registry)


def extract_xml(root: XMLNode, rule: XMLRule) -> CollectedData | None:
    data: dict[str, Any] = {}

    subroots = [root] if rule.foreach is None else rule.foreach.select(root)
    for subroot in subroots:
        if rule.extractor.foreach is None:
            value = rule.extractor.extract(subroot)
            if value is None:
                continue
            for transform in rule.extractor.transformers:
                value = transform(value)
        else:
            raws = [rule.extractor.extract(n)
                    for n in rule.extractor.foreach.select(subroot)]
            value = [v for v in raws if v is not None]
            if len(value) == 0:
                continue
            if len(rule.extractor.transforms) > 0:
                for i in range(len(value)):
                    for transform in rule.extractor.transformers:
                        value[i] = transform(value[i])

        for transform in rule.transformers:
            value = transform(value)

        if isinstance(rule.key, str):
            key = rule.key
        else:
            key = rule.key.extract(subroot)
            for key_transform in rule.key.transformers:
                key = key_transform(key)
        data[key] = value

    return data if len(data) > 0 else None


def extract_json(root: JSONNode, rule: JSONRule) -> CollectedData | None:
    data: dict[str, Any] = {}

    subroots = [root] if rule.foreach is None else rule.foreach.select(root)
    for subroot in subroots:
        if rule.extractor.foreach is None:
            value = rule.extractor.extract(subroot)
            if value is None:
                continue
            for transform in rule.extractor.transformers:
                value = transform(value)
        else:
            raws = [rule.extractor.extract(n)
                    for n in rule.extractor.foreach.select(subroot)]
            value = [v for v in raws if v is not None]
            if len(value) == 0:
                continue
            if len(rule.extractor.transforms) > 0:
                for i in range(len(value)):
                    for transform in rule.extractor.transformers:
                        value[i] = transform(value[i])

        for transform in rule.transformers:
            value = transform(value)

        if isinstance(rule.key, str):
            key = rule.key
        else:
            key = rule.key.extract(subroot)
            for key_transform in rule.key.transformers:
                key = key_transform(key)
        data[key] = value

    return data if len(data) > 0 else None


def collect_xml(root: XMLNode, rules: list[XMLRule]) -> CollectedData | None:
    data: dict[str, Any] = {}
    for rule in rules:
        subdata = extract_xml(root, rule)
        if subdata is not None:
            data.update(subdata)
    return data if len(data) > 0 else None


def collect_json(root: JSONNode, rules: list[JSONRule]) -> CollectedData | None:  # noqa: E501
    data: dict[str, Any] = {}
    for rule in rules:
        subdata = extract_json(root, rule)
        if subdata is not None:
            data.update(subdata)
    return data if len(data) > 0 else None


@dataclass(kw_only=True)
class _Spec:
    doctype: DocType
    pre: list[str] = field(default_factory=list)
    post: list[str] = field(default_factory=list)

    preprocessors: list[Preprocessor] = field(default_factory=list)
    postprocessors: list[Postprocessor] = field(default_factory=list)

    def set_preprocessors(self, registry: Mapping[str, Preprocessor]) -> None:
        self.preprocessors = [registry[name] for name in self.pre]

    def set_postprocessors(self, registry: Mapping[str, Postprocessor]) -> None:  # noqa: E501
        self.postprocessors = [registry[name] for name in self.post]


@dataclass(kw_only=True)
class XMLSpec(_Spec):
    path_type: Literal["xpath"] = "xpath"
    rules: list[XMLRule] = field(default_factory=list)

    def set_transformers(self, registry: Mapping[str, Transformer]) -> None:
        for rule in self.rules:
            rule.set_transformers(registry)


@dataclass(kw_only=True)
class JSONSpec(_Spec):
    path_type: Literal["jmespath"] = "jmespath"
    rules: list[JSONRule] = field(default_factory=list)

    def set_transformers(self, registry: Mapping[str, Transformer]) -> None:
        for rule in self.rules:
            rule.set_transformers(registry)


def load_spec(
        content: dict,
        *,
        transformers: Mapping[str, Transformer] = _EMPTY_REGISTRY,
        preprocessors: Mapping[str, Preprocessor] = _EMPTY_REGISTRY,
        postprocessors: Mapping[str, Postprocessor] = _EMPTY_REGISTRY,
) -> XMLSpec | JSONSpec:
    spec: XMLSpec | JSONSpec = deserialize(
        content,
        type_=Union[XMLSpec, JSONSpec],
        strconstructed={XMLPath, JSONPath},
        failonextra=True,
    )
    spec.set_preprocessors(preprocessors)
    spec.set_postprocessors(postprocessors)
    spec.set_transformers(transformers)
    return spec


def scrape(document: str, spec: XMLSpec | JSONSpec) -> CollectedData:
    root = _PARSERS[spec.doctype](document)
    for preprocess in spec.preprocessors:
        root = preprocess(root)
    match (root, spec):
        case (XMLNode(), XMLSpec()):
            data = collect_xml(root, spec.rules)
        case (JSONNode(), JSONSpec()):
            data = collect_json(root, spec.rules)
        case _:
            raise TypeError("Node and spec types don't match")
    if data is None:
        return {}
    for postprocess in spec.postprocessors:
        data = postprocess(data)
    return data
