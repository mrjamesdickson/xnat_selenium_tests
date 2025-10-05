"""Version-aware page object registry inspired by the Bitbucket suite."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple, Type


class XnatPageComponent:
    """Base class for page components bound to XNAT versions."""

    handled_versions: Sequence[Type["XnatVersion"]] = ()

    @classmethod
    def get_handled_versions(cls) -> Tuple[Type["XnatVersion"], ...]:
        return tuple(cls.handled_versions)


class XnatVersion:
    """Marker base class for XNAT versions."""


class PageObjectRegistry:
    """Registry mapping base components to version specific subclasses."""

    _registry: Dict[Type[XnatPageComponent], List[Type[XnatPageComponent]]] = {}

    @classmethod
    def register(cls, component: Type[XnatPageComponent]) -> Type[XnatPageComponent]:
        root = cls._root_component(component)
        cls._registry.setdefault(root, [])
        if component not in cls._registry[root]:
            cls._registry[root].append(component)
        return component

    @classmethod
    def clear(cls) -> None:
        cls._registry.clear()

    @classmethod
    def get_page_object(
        cls, base_component: Type[XnatPageComponent], version: Type["XnatVersion"]
    ) -> Type[XnatPageComponent]:
        root = cls._root_component(base_component)
        candidates = cls._registry.get(root, [])
        # Prefer most derived classes first
        ordered = sorted(
            candidates,
            key=lambda component: (-cls._depth(component, root), -len(component.get_handled_versions())),
        )
        for component in ordered:
            if version in component.get_handled_versions():
                return component
        return base_component

    @staticmethod
    def _root_component(component: Type[XnatPageComponent]) -> Type[XnatPageComponent]:
        root = component
        for base in component.mro():
            if issubclass(base, XnatPageComponent) and base is not XnatPageComponent:
                root = base
        return root

    @staticmethod
    def _depth(component: Type[XnatPageComponent], root: Type[XnatPageComponent]) -> int:
        depth = 0
        current = component
        while current is not root and current is not XnatPageComponent:
            current = current.__mro__[1]
            depth += 1
        return depth


@dataclass
class Xnat_1_7_7(XnatVersion):
    pass


@dataclass
class Xnat_1_7_5_2(XnatVersion):
    pass


@dataclass
class Xnat_1_7_5(XnatVersion):
    pass


@dataclass
class Xnat_1_7_4(XnatVersion):
    pass


@dataclass
class Xnat_1_7_3(XnatVersion):
    pass


@dataclass
class Xnat_1_7_2(XnatVersion):
    pass


@dataclass
class Xnat_1_6dev(XnatVersion):
    pass

