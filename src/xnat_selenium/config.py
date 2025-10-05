"""Configuration helpers for the XNAT Selenium test-suite."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class XnatConfig:
    """Container for runtime configuration values."""

    base_url: str
    username: str
    password: str
    headless: bool = True

    @classmethod
    def from_env(cls, *, base_url: str | None = None, username: str | None = None, password: str | None = None, headless: bool | None = None) -> "XnatConfig":
        resolved_base_url = base_url or os.getenv("XNAT_BASE_URL")
        resolved_username = username or os.getenv("XNAT_USERNAME")
        resolved_password = password or os.getenv("XNAT_PASSWORD")
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
