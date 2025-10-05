"""Navigation and session management tests for the XNAT UI."""
from __future__ import annotations

import pytest

from xnat_selenium.pages.dashboard import DashboardPage
from xnat_selenium.pages.login import LoginPage
from xnat_selenium.pages.projects import ProjectsPage


@pytest.mark.smoke
@pytest.mark.projects
def test_dashboard_links_to_projects(dashboard, xnat_config):
    """Selecting the projects option should load the project listing."""

    dashboard.go_to_projects()

    projects_page = ProjectsPage(dashboard.driver, xnat_config.base_url)
    assert projects_page.is_loaded(), "Projects page did not finish loading"


@pytest.mark.smoke
def test_user_can_logout(driver, xnat_config):
    """Logging out returns the user to the login screen."""

    login_page = LoginPage(driver, xnat_config.base_url).open()
    login_page.login(xnat_config.username, xnat_config.password)

    dashboard = DashboardPage(driver, xnat_config.base_url)
    dashboard.wait_until_loaded()
    dashboard.logout()

    login_page = LoginPage(driver, xnat_config.base_url)
    assert login_page.is_displayed(), "Login screen was not displayed after logout"
