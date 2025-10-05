"""Utility classes for composing XPaths mirroring the Groovy helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class XpathLocator:
    expression: str

    def join_sublocator(self, sublocator: str) -> "XpathLocator":
        trimmed = sublocator.strip()
        if trimmed.startswith("./"):
            trimmed = trimmed[2:]
        elif trimmed.startswith("/"):
            trimmed = trimmed[1:]
        if not trimmed:
            return XpathLocator(self.expression)
        return XpathLocator(f"{self.expression}/{trimmed}")

    def nth_instance(self, index: int) -> "XpathLocator":
        return XpathLocator(f"({self.expression})[{index}]")

    def parent(self) -> "XpathLocator":
        return XpathLocator(f"{self.expression}/..")

    def grandparent(self) -> "XpathLocator":
        return XpathLocator(f"{self.expression}/../..")

    def union_sublocators(self, sublocators: Sequence["XpathLocator"]) -> "XpathUnion":
        joined = [self.join_sublocator(locator.expression) for locator in sublocators]
        return XpathUnion(joined)


@dataclass(frozen=True)
class XpathUnion:
    locators: Sequence[XpathLocator]

    @property
    def expression(self) -> str:
        joined = " | ".join(locator.expression for locator in self.locators)
        return f"({joined})"

