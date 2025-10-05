"""Authentication focused tests."""
from __future__ import annotations

import pytest

from xnat_selenium.pages.dashboard import DashboardPage
from xnat_selenium.pages.login import LoginPage


@pytest.mark.smoke
def test_successful_login(driver, xnat_config):
    """Users with valid credentials should land on the dashboard."""
    login_page = LoginPage(driver, xnat_config.base_url).open()
    login_page.login(xnat_config.username, xnat_config.password)

    dashboard = DashboardPage(driver, xnat_config.base_url)
    dashboard.wait_until_loaded()
    assert dashboard.welcome_message()
    dashboard.logout()


@pytest.mark.parametrize(
    "username,password",
    [
        ("", ""),
        ("invalid", "credentials"),
    ],
)
def test_login_failure(driver, xnat_config, username, password):
    """Invalid credentials should display an error message."""
    login_page = LoginPage(driver, xnat_config.base_url).open()
    login_page.login(username or xnat_config.username, password)

    assert login_page.error_message()
