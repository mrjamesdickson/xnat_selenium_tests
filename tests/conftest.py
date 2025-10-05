"""Pytest configuration and shared fixtures for the XNAT Selenium suite."""
from __future__ import annotations

import os
from typing import Generator

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from xnat_selenium.config import XnatConfig
from xnat_selenium.pages.dashboard import DashboardPage
from xnat_selenium.pages.login import LoginPage


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("xnat")
    group.addoption("--base-url", action="store", dest="base_url", help="Base URL of the XNAT instance")
    group.addoption("--username", action="store", dest="username", help="XNAT username to authenticate with")
    group.addoption("--password", action="store", dest="password", help="XNAT password to authenticate with")
    group.addoption("--browser", action="store", dest="browser", default="chrome", help="Browser to use (chrome|firefox|edge)")
    group.addoption("--remote-url", action="store", dest="remote_url", help="URL of a remote Selenium server")
    group.addoption("--headed", action="store_true", dest="headed", help="Run browsers in headed mode")


@pytest.fixture(scope="session")
def xnat_config(pytestconfig: pytest.Config) -> XnatConfig:
    try:
        return XnatConfig.from_env(
            base_url=pytestconfig.getoption("base_url"),
            username=pytestconfig.getoption("username"),
            password=pytestconfig.getoption("password"),
            headless=not pytestconfig.getoption("headed"),
        )
    except ValueError as exc:
        pytest.skip(str(exc))


def _build_driver(browser: str, *, headless: bool, remote_url: str | None) -> webdriver.Remote:
    browser = browser.lower()
    if browser == "chrome":
        options = ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        if remote_url:
            return webdriver.Remote(command_executor=remote_url, options=options)
        return webdriver.Chrome(options=options)
    if browser == "firefox":
        options = FirefoxOptions()
        options.set_preference("dom.webnotifications.enabled", False)
        options.set_preference("media.navigator.streams.fake", True)
        options.headless = headless
        if remote_url:
            return webdriver.Remote(command_executor=remote_url, options=options)
        return webdriver.Firefox(options=options)
    if browser == "edge":
        options = EdgeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        if remote_url:
            return webdriver.Remote(command_executor=remote_url, options=options)
        return webdriver.Edge(options=options)
    raise pytest.UsageError(f"Unsupported browser '{browser}'. Use chrome, firefox, or edge.")


@pytest.fixture(scope="session")
def driver(pytestconfig: pytest.Config, xnat_config: XnatConfig) -> Generator[webdriver.Remote, None, None]:
    remote_url = pytestconfig.getoption("remote_url") or os.getenv("SELENIUM_REMOTE_URL")
    try:
        driver_instance = _build_driver(
            pytestconfig.getoption("browser"), headless=xnat_config.headless, remote_url=remote_url
        )
    except WebDriverException as exc:  # pragma: no cover - exercised at runtime
        pytest.skip(f"Unable to start Selenium driver: {exc}")
    driver_instance.set_page_load_timeout(60)
    driver_instance.implicitly_wait(2)
    yield driver_instance
    driver_instance.quit()


@pytest.fixture
def dashboard(driver: webdriver.Remote, xnat_config: XnatConfig) -> Generator[DashboardPage, None, None]:
    login_page = LoginPage(driver, xnat_config.base_url).open()
    login_page.login(xnat_config.username, xnat_config.password)
    dashboard_page = DashboardPage(driver, xnat_config.base_url)
    dashboard_page.wait_until_loaded()
    try:
        yield dashboard_page
    finally:
        try:
            dashboard_page.logout()
        except Exception:  # pragma: no cover - best effort logout
            pass
