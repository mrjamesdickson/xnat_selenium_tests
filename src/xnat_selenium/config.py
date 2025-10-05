"""Configuration helpers for the XNAT Selenium test-suite."""
from __future__ import annotations

import os
from dataclasses import dataclass

from .mock_driver import is_mock_base_url


def _env_flag(value: str | None) -> bool:
    if value is None:
        return False
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class XnatConfig:
    """Container for runtime configuration values."""

    base_url: str
    username: str
    password: str
    headless: bool = True

    @classmethod
    def from_env(cls, *, base_url: str | None = None, username: str | None = None, password: str | None = None, headless: bool | None = None) -> "XnatConfig":
        requested_mock = _env_flag(os.getenv("XNAT_USE_MOCK")) or (base_url is not None and is_mock_base_url(base_url))

        resolved_base_url = base_url or os.getenv("XNAT_BASE_URL")
        resolved_username = username or os.getenv("XNAT_USERNAME")
        env_password = os.getenv("XNAT_PASSWORD")
        resolved_password = password if password is not None else env_password

        if requested_mock:
            resolved_base_url = resolved_base_url or "mock://xnat"
            resolved_username = resolved_username or "admin"
            resolved_password = resolved_password if resolved_password is not None else "admin"

        resolved_headless = headless if headless is not None else os.getenv("XNAT_HEADLESS", "1") not in {"0", "false", "False"}

        if not resolved_base_url:
            raise ValueError("XNAT base URL must be provided via --base-url or XNAT_BASE_URL")
        if not resolved_username:
            raise ValueError("XNAT username must be provided via --username or XNAT_USERNAME")
        if resolved_password is None:
            raise ValueError("XNAT password must be provided via --password or XNAT_PASSWORD")

        return cls(
            base_url=resolved_base_url.rstrip("/"),
            username=resolved_username,
            password=resolved_password,
            headless=resolved_headless,
        )
