"""Page objects that model the main XNAT dashboard after login."""
from __future__ import annotations

from selenium.webdriver.common.by import By

from .base import BasePage


class DashboardPage(BasePage):
    """Landing page once a user authenticates to XNAT."""

    path = "/"

    _welcome_banner = (By.CSS_SELECTOR, "#main_nav, body")
    _browse_menu = (By.CSS_SELECTOR, "a[href='#browse'], li.more a:contains('Browse')")
    _all_projects_link = (By.CSS_SELECTOR, "#browse-projects-menu-item, a.nolink:contains('All Projects')")
    _logout_link = (By.ID, "logout_user")

    def wait_until_loaded(self) -> None:
        # Wait for main navigation to be visible (confirms page loaded)
        self.wait_for_visibility(self._welcome_banner)

    def go_to_projects(self) -> None:
        # In modern XNAT, projects are shown on the home page in dropdown menus.
        # We just stay on the dashboard since it already shows projects.
        # Check for the presence of the projects menu (it may be hidden in a dropdown)
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
        wait = WebDriverWait(self.driver, self.timeout)
        wait.until(EC.presence_of_element_located((By.ID, "browse-projects-menu-item")))

    def welcome_message(self) -> str:
        """Return the welcome banner text displayed on the dashboard."""
        return self.text_of(self._welcome_banner)

    def logout(self) -> None:
        self.click(self._logout_link)
