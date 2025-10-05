"""Shared helpers for interacting with XNAT pages via Selenium.

This module provides a small convenience wrapper around ``WebDriver`` to make
explicit waits, navigation, and logging consistent across the page objects used
in the test-suite.
"""
from __future__ import annotations

import logging
from typing import Callable, Iterable, Optional, Tuple

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

Locator = Tuple[str, str]

LOGGER = logging.getLogger(__name__)


class BasePage:
    """Base implementation for all XNAT page objects.

    Parameters
    ----------
    driver:
        The Selenium ``WebDriver`` instance used for the current test run.
    base_url:
        The base URL of the XNAT deployment under test.
    timeout:
        Default explicit wait timeout, in seconds.
    """

    def __init__(self, driver: WebDriver, base_url: str, timeout: int = 20) -> None:
        self.driver = driver
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------
    def visit(self, path: str) -> None:
        """Navigate to a path relative to ``base_url``."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        LOGGER.debug("Navigating to %s", url)
        self.driver.get(url)

    # ------------------------------------------------------------------
    # Waiting helpers
    # ------------------------------------------------------------------
    def wait_for_visibility(self, locator: Locator, timeout: Optional[int] = None):
        """Wait until an element located by ``locator`` is visible."""
        LOGGER.debug("Waiting for visibility of %s", locator)
        wait = WebDriverWait(self.driver, timeout or self.timeout)
        return wait.until(EC.visibility_of_element_located(locator))

    def wait_for_clickable(self, locator: Locator, timeout: Optional[int] = None):
        """Wait until an element located by ``locator`` can be clicked."""
        LOGGER.debug("Waiting for clickability of %s", locator)
        wait = WebDriverWait(self.driver, timeout or self.timeout)
        return wait.until(EC.element_to_be_clickable(locator))

    def wait_until(self, condition: Callable[[WebDriver], bool], *, timeout: Optional[int] = None, message: str = "") -> None:
        """Wait until a custom ``condition`` returns ``True``."""
        LOGGER.debug("Waiting until condition %s", message or condition)
        wait = WebDriverWait(self.driver, timeout or self.timeout)
        try:
            wait.until(condition, message)
        except TimeoutException as exc:  # pragma: no cover - defensive logging
            LOGGER.error("Timeout while waiting for condition %s: %s", message, exc)
            raise

    # ------------------------------------------------------------------
    # Element interaction helpers
    # ------------------------------------------------------------------
    def click(self, locator: Locator) -> None:
        element = self.wait_for_clickable(locator)
        LOGGER.debug("Clicking element %s", locator)
        element.click()

    def fill(self, locator: Locator, value: str, *, clear: bool = True) -> None:
        from selenium.common.exceptions import InvalidElementStateException
        from selenium.webdriver.common.keys import Keys

        element = self.wait_for_visibility(locator)
        LOGGER.debug("Typing in element %s", locator)
        if clear:
            try:
                element.clear()
            except InvalidElementStateException:
                # If clear() fails, try selecting all and deleting
                try:
                    element.send_keys(Keys.CONTROL + "a")
                    element.send_keys(Keys.DELETE)
                except Exception:
                    # If that also fails, just proceed without clearing
                    LOGGER.debug("Unable to clear element %s, proceeding without clearing", locator)
        element.send_keys(value)

    def text_of(self, locator: Locator) -> str:
        element = self.wait_for_visibility(locator)
        text = element.text.strip()
        LOGGER.debug("Text of %s: %s", locator, text)
        return text

    def elements(self, locator: Locator):
        LOGGER.debug("Finding elements %s", locator)
        return self.driver.find_elements(*locator)

    def any_visible(self, locators: Iterable[Locator], timeout: Optional[int] = None) -> Locator:
        """Wait until any of the provided locators is visible.

        The locator that first becomes visible is returned.
        """
        wait = WebDriverWait(self.driver, timeout or self.timeout)
        for locator in locators:
            try:
                wait.until(EC.visibility_of_element_located(locator))
                return locator
            except TimeoutException:
                continue
        raise TimeoutException("None of the provided locators became visible")
