"""Page objects that model the main XNAT dashboard after login."""
from __future__ import annotations

from selenium.webdriver.common.by import By

from .base import BasePage


class DashboardPage(BasePage):
    """Landing page once a user authenticates to XNAT."""

    path = "/app/template/XDATScreen_select_project.vm"

    _welcome_banner = (By.CSS_SELECTOR, "#page-content h1, .welcome-message")
    _projects_link = (By.CSS_SELECTOR, "a[href*='projects'], a[href*='SelectProject']")
    _user_menu = (By.CSS_SELECTOR, "#user-box, .user-menu")
    _logout_link = (By.CSS_SELECTOR, "a[href*='Logout']")

    def wait_until_loaded(self) -> None:
        self.wait_for_visibility(self._welcome_banner)

    def go_to_projects(self) -> None:
        self.click(self._projects_link)

    def welcome_message(self) -> str:
        """Return the welcome banner text displayed on the dashboard."""
        return self.text_of(self._welcome_banner)

    def logout(self) -> None:
        self.click(self._user_menu)
        self.click(self._logout_link)
