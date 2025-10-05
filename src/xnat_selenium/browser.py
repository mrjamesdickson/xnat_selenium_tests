"""Minimal browser support registry mirroring the legacy suite."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Dict, Type


@dataclass(frozen=True)
class BaseBrowserSupport:
    """Base class for browser-specific capabilities."""

    name: ClassVar[str] = ""


class ChromeSupport(BaseBrowserSupport):
    name = "Chrome"


class FirefoxSupport(BaseBrowserSupport):
    name = "MozillaFirefox"


class BrowserSupport:
    """Cache for browser support helpers used by the selenium suite."""

    _ALIASES: ClassVar[Dict[str, Type[BaseBrowserSupport]]] = {
        "chrome": ChromeSupport,
        "google chrome": ChromeSupport,
        "mozilla firefox": FirefoxSupport,
        "firefox": FirefoxSupport,
        "ff": FirefoxSupport,
    }
    cached_browser_support: ClassVar[Type[BaseBrowserSupport] | None] = None

    @classmethod
    def cache_browser(cls, browser_key: str) -> None:
        """Cache the browser support class for ``browser_key``."""

        normalized = browser_key.strip().lower()
        support_cls = cls._ALIASES.get(normalized)
        if support_cls is None:
            known = sorted({support.name for support in cls._ALIASES.values()})
            options = ", ".join(known)
            raise RuntimeError(
                f"Unknown browser: {browser_key}. Available browser helpers: {options}"
            )
        cls.cached_browser_support = support_cls

    @classmethod
    def clear_cache(cls) -> None:
        cls.cached_browser_support = None

