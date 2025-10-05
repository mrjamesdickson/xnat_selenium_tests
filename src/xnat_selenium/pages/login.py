"""Page object modelling the XNAT login screen."""
from __future__ import annotations

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By

from .base import BasePage


class LoginPage(BasePage):
    """Interact with the XNAT login page."""

    # The login view can be reached via ``/`` or ``/app/template/Login.vm``.
    path = "/app/template/Login.vm"

    _username_input = (By.CSS_SELECTOR, "input[name='login'], input[name='username']")
    _password_input = (By.NAME, "password")
    _submit_button = (By.CSS_SELECTOR, "form button[type='submit'], form input[type='submit'], button#loginButton")
    _error_banner_locators = (
        (By.CSS_SELECTOR, ".message, .alert-error, .message-error, .error"),
        (By.CSS_SELECTOR, ".alert.alert-danger, .alert.alert-error, .xnat-alert-error"),
        (By.ID, "loginMessage"),
        (By.ID, "login-error"),
        (By.CSS_SELECTOR, "[role='alert'], [data-testid='login-error']"),
    )

    def open(self) -> "LoginPage":
        self.visit(self.path)
        # XNAT redirects logged-in users away from the login page.
        # Only wait for the username input if we're actually on the login page.
        if "/Login" in self.driver.current_url or "login" in self.driver.current_url.lower():
            self.wait_for_visibility(self._username_input)
        return self

    def login(self, username: str, password: str) -> None:
        self.fill(self._username_input, username)
        self.fill(self._password_input, password)
        self.click(self._submit_button)

    def _extract_banner_text(self, locator: tuple[str, str]) -> str:
        try:
            element = self.wait_for_visibility(locator, timeout=5)
        except (TimeoutException, StaleElementReferenceException):
            return ""

        text = (element.text or "").strip()
        if text:
            return text
        try:
            raw = element.get_attribute("textContent") or ""
        except Exception:  # pragma: no cover - defensive in case drivers differ
            raw = ""
        return raw.strip()

    def error_message(self) -> str:
        """Return any validation or authentication message shown on login failure."""

        try:
            locator = self.any_visible(self._error_banner_locators, timeout=5)
            message = self._extract_banner_text(locator)
            if message:
                return message
        except TimeoutException:
            pass

        # Retry locating banners directly in case the DOM mutated between waits.
        for locator in self._error_banner_locators:
            try:
                element = self.driver.find_element(*locator)
            except NoSuchElementException:
                continue
            except Exception:  # pragma: no cover - browser specific edge cases
                continue
            text = (element.text or "").strip()
            if not text:
                try:
                    text = (element.get_attribute("textContent") or "").strip()
                except Exception:  # pragma: no cover
                    text = ""
            if text:
                return text

        # Fallback to built-in browser validation messages when HTML5 validation
        # prevents form submission (e.g. empty required fields).
        for locator in (self._username_input, self._password_input):
            try:
                field = self.driver.find_element(*locator)
            except NoSuchElementException:
                continue
            except Exception:  # pragma: no cover
                continue
            try:
                message = field.get_attribute("validationMessage") or ""
            except Exception:  # pragma: no cover
                message = ""
            message = message.strip()
            if message:
                return message

        return ""

    def is_displayed(self, *, timeout: int | None = None) -> bool:
        """Return ``True`` when the login form is visible."""

        try:
            self.wait_for_visibility(self._username_input, timeout=timeout)
            return True
        except TimeoutException:
            return False
