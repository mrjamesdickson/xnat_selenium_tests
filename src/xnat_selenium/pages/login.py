"""Page object modelling the XNAT login screen."""
from __future__ import annotations

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from .base import BasePage


class LoginPage(BasePage):
    """Interact with the XNAT login page."""

    # The login view can be reached via ``/`` or ``/app/template/Login.vm``.
    path = "/app/template/Login.vm"

    _username_input = (By.CSS_SELECTOR, "input[name='login'], input[name='username']")
    _password_input = (By.NAME, "password")
    _submit_button = (By.CSS_SELECTOR, "form button[type='submit'], form input[type='submit'], button#loginButton")
    _error_banner = (By.CSS_SELECTOR, ".message, .alert-error, .message-error, .error")

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

    def error_message(self) -> str:
        import time
        from selenium.common.exceptions import StaleElementReferenceException
        try:
            return self.text_of(self._error_banner)
        except (TimeoutException, StaleElementReferenceException):
            # If there's no error banner or stale element, wait and retry once
            time.sleep(1)
            try:
                # Try to find the error banner again after page reload
                return self.text_of(self._error_banner)
            except (TimeoutException, StaleElementReferenceException):
                # If still no error banner, check if we're still on the login page
                # (which would indicate form validation prevented submission)
                if "/Login" in self.driver.current_url or "login" in self.driver.current_url.lower():
                    # Still on login page - check if password field is empty
                    try:
                        password_field = self.driver.find_element(By.NAME, "password")
                        if not password_field.get_attribute("value"):
                            return "Form validation error (required field empty)"
                    except:
                        pass
                return ""

    def is_displayed(self, *, timeout: int | None = None) -> bool:
        """Return ``True`` when the login form is visible."""

        try:
            self.wait_for_visibility(self._username_input, timeout=timeout)
            return True
        except TimeoutException:
            return False
