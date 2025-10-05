"""Utilities for marshalling element specifications from the legacy suite."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, List, Mapping, Sequence

import yaml


class _ElementSpecLoader(yaml.SafeLoader):
    pass


def _text_index_array_constructor(loader: yaml.Loader, node: yaml.Node) -> Any:
    mapping = loader.construct_mapping(node)
    mapping["type"] = "textIndexArray"
    return mapping


_ElementSpecLoader.add_constructor("!textIndexArray", _text_index_array_constructor)
_ElementSpecLoader.add_constructor("!<textIndexArray>", _text_index_array_constructor)
_ElementSpecLoader.add_constructor("textIndexArray", _text_index_array_constructor)


def _is_numeric(value: Any) -> bool:
    if isinstance(value, (int, float, Decimal)):
        return True
    if isinstance(value, str):
        try:
            Decimal(value)
        except Exception:
            return False
        return True
    return False


def _to_decimal(value: Any) -> Any:
    if _is_numeric(value):
        return Decimal(str(value))
    return value


@dataclass(frozen=True)
class Locator:
    type: str
    value: str

    @classmethod
    def from_yaml(cls, payload: Any) -> "Locator":
        if isinstance(payload, str):
            return cls(type="xpath", value=payload)
        if isinstance(payload, Mapping):
            locator_type = payload.get("type", "xpath")
            value = payload.get("value")
            if value is None:
                raise ValueError("Locator payload missing 'value'")
            return cls(type=str(locator_type), value=str(value))
        raise TypeError(f"Unsupported locator payload: {payload!r}")

    def to_yaml(self) -> Any:
        if self.type.lower() == "xpath":
            return self.value
        return {"type": self.type, "value": self.value}


@dataclass(frozen=True)
class Element:
    locator: Locator
    value: Any

    @classmethod
    def from_yaml(cls, payload: Mapping[str, Any]) -> "Element":
        locator = Locator.from_yaml(payload["locator"])
        value = _to_decimal(payload["value"])
        return cls(locator=locator, value=value)

    def formatted_value(self) -> str:
        if isinstance(self.value, Decimal):
            return format(self.value, "f")
        return str(self.value)

    def to_yaml(self) -> Mapping[str, Any]:
        return {"locator": self.locator.to_yaml(), "value": self.value}


class Comparator:
    def to_yaml_blocks(self) -> List[str]:  # pragma: no cover - abstract
        raise NotImplementedError


@dataclass(frozen=True)
class EqualityElementComparator(Comparator):
    elements: Sequence[Element] = field(default_factory=list)

    def to_yaml_blocks(self) -> List[str]:
        lines = ["- type: Equals", "  elements:"]
        for element in self.elements:
            locator = element.locator.to_yaml()
            if isinstance(locator, str):
                lines.append(f"  - locator: \"{locator}\"")
            else:
                lines.append("  - locator:")
                lines.append(f"      type: {locator['type']}")
                lines.append(f"      value: {locator['value']}")
            lines.append(f"    value: {element.formatted_value()}")
        return lines


@dataclass(frozen=True)
class MaxPercentToleranceElementComparator(Comparator):
    tolerance: Decimal
    elements: Sequence[Element] = field(default_factory=list)

    def to_yaml_blocks(self) -> List[str]:
        lines = ["- type: maxPercentTolerance", f"  percent: {format(self.tolerance, 'f')}", "  elements:"]
        for element in self.elements:
            locator = element.locator.to_yaml()
            if isinstance(locator, str):
                lines.append(f"  - locator: \"{locator}\"")
            else:
                lines.append("  - locator:")
                lines.append(f"      type: {locator['type']}")
                lines.append(f"      value: {locator['value']}")
            lines.append(f"    value: {element.formatted_value()}")
        return lines


@dataclass(frozen=True)
class TextIndexArray:
    id: str
    locator: str
    offset: int
    type: str = "textIndexArray"

    @classmethod
    def from_yaml(cls, payload: Mapping[str, Any]) -> "TextIndexArray":
        return cls(
            id=str(payload["id"]),
            locator=str(payload["locator"]),
            offset=int(payload["offset"]),
        )

    def to_yaml_blocks(self) -> List[str]:
        return [
            f"- !<{self.type}>",
            f"  id: {self.id}",
            f"  locator: \"{self.locator}\"",
            f"  offset: {self.offset}",
        ]


@dataclass(frozen=True)
class ElementSpecifications:
    comparators: Sequence[Comparator]
    locator_caches: Sequence[TextIndexArray]
    locator_replacements: Mapping[str, str]

    @classmethod
    def from_yaml(cls, payload: str) -> "ElementSpecifications":
        data = yaml.load(payload, Loader=_ElementSpecLoader)
        comparators = []
        for comparator_payload in data.get("comparators", []):
            comparator_type = comparator_payload.get("type")
            elements = [
                Element.from_yaml(element_payload)
                for element_payload in comparator_payload.get("elements", [])
            ]
            if comparator_type == "Equals":
                comparators.append(EqualityElementComparator(tuple(elements)))
            elif comparator_type == "maxPercentTolerance":
                tolerance = Decimal(str(comparator_payload.get("percent", 0)))
                comparators.append(
                    MaxPercentToleranceElementComparator(tolerance, tuple(elements))
                )
            else:
                raise ValueError(f"Unsupported comparator type: {comparator_type}")

        locator_caches = [
            TextIndexArray.from_yaml(cache_payload)
            for cache_payload in data.get("locatorCaches", [])
        ]
        locator_replacements = data.get("locatorReplacements", {})
        return cls(
            comparators=tuple(comparators),
            locator_caches=tuple(locator_caches),
            locator_replacements=dict(locator_replacements),
        )

    def to_yaml(self) -> str:
        lines: List[str] = ["comparators:"]
        for comparator in self.comparators:
            lines.extend(comparator.to_yaml_blocks())
        lines.append("locatorCaches:")
        for cache in self.locator_caches:
            lines.extend(cache.to_yaml_blocks())
        lines.append("locatorReplacements:")
        for key, value in self.locator_replacements.items():
            lines.append(f"  {key}: \"{value}\"")
        return "\n".join(lines) + "\n"

