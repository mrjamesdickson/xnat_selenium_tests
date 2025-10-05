"""Page object modelling the XNAT login screen."""
from __future__ import annotations

from selenium.webdriver.common.by import By

from .base import BasePage


class LoginPage(BasePage):
    """Interact with the XNAT login page."""

    # The login view can be reached via ``/`` or ``/app/template/Login.vm``.
    path = "/app/template/Login.vm"

    _username_input = (By.NAME, "login")
    _password_input = (By.NAME, "password")
    _submit_button = (By.CSS_SELECTOR, "form button[type='submit'], form input[type='submit']")
    _error_banner = (By.CSS_SELECTOR, ".alert-error, .message-error, .error")

    def open(self) -> "LoginPage":
        self.visit(self.path)
        self.wait_for_visibility(self._username_input)
        return self

    def login(self, username: str, password: str) -> None:
        self.fill(self._username_input, username)
        self.fill(self._password_input, password)
        self.click(self._submit_button)

    def error_message(self) -> str:
        return self.text_of(self._error_banner)
