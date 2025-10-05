"""Project management scenarios inspired by the upstream Bitbucket suite."""
from __future__ import annotations

import uuid

import pytest

from xnat_selenium.pages.dashboard import DashboardPage
from xnat_selenium.pages.login import LoginPage
from xnat_selenium.pages.projects import Project, ProjectsPage


def _login_to_dashboard(driver, xnat_config) -> DashboardPage:
    login_page = LoginPage(driver, xnat_config.base_url).open()
    login_page.login(xnat_config.username, xnat_config.password)
    dashboard = DashboardPage(driver, xnat_config.base_url)
    dashboard.wait_until_loaded()
    return dashboard


@pytest.mark.projects
def test_project_description_persisted_in_listing(driver, xnat_config):
    """Creating a project with a description should display that description."""

    dashboard = _login_to_dashboard(driver, xnat_config)
    project_id = f"AUTO{uuid.uuid4().hex[:6]}"
    project = Project(identifier=project_id, name=f"Project {project_id}", description="Functional imaging study")

    try:
        dashboard.go_to_projects()
        projects_page = ProjectsPage(driver, xnat_config.base_url)
        projects_page.open()
        projects_page.create_project(project)
        projects_page.open()

        rows = projects_page.project_rows()
        matching_rows = [row for row in rows if project.identifier in row]
        assert matching_rows, "Project was not listed after creation"
        assert project.description in matching_rows[0], "Project description was not rendered in the listing"
    finally:
        DashboardPage(driver, xnat_config.base_url).logout()


@pytest.mark.projects
def test_recreating_project_updates_existing_entry(driver, xnat_config):
    """Reusing an identifier should update the existing project record instead of duplicating it."""

    dashboard = _login_to_dashboard(driver, xnat_config)
    project_id = f"AUTO{uuid.uuid4().hex[:6]}"
    original = Project(identifier=project_id, name=f"Baseline {project_id}", description="Initial")
    updated = Project(identifier=project_id, name=f"Updated {project_id}", description="Updated description")

    try:
        dashboard.go_to_projects()
        projects_page = ProjectsPage(driver, xnat_config.base_url)
        projects_page.open()
        projects_page.create_project(original)
        projects_page.open()
        projects_page.create_project(updated)
        projects_page.open()

        rows = projects_page.project_rows()
        matching_rows = [row for row in rows if project_id in row]
        assert matching_rows, "Updated project was not listed"
        row_text = matching_rows[0]
        assert updated.name in row_text, "Project name was not updated when reusing the identifier"
        assert updated.description in row_text, "Project description was not updated when reusing the identifier"
        assert original.description not in row_text, "Stale project details remained after update"
    finally:
        DashboardPage(driver, xnat_config.base_url).logout()


@pytest.mark.projects
def test_project_creation_requires_identifier_and_name(driver, xnat_config):
    """Attempting to submit an incomplete project form should not add rows to the listing."""

    dashboard = _login_to_dashboard(driver, xnat_config)
    project_id = f"AUTO{uuid.uuid4().hex[:6]}"

    try:
        dashboard.go_to_projects()
        projects_page = ProjectsPage(driver, xnat_config.base_url)
        projects_page.open()
        initial_count = projects_page.project_count()

        # Missing identifier
        projects_page.start_project_creation()
        projects_page.enter_project_details(name="Missing Identifier")
        projects_page.submit_project_form()
        assert projects_page.project_count() == initial_count, "Project without identifier should not be created"

        # Missing name
        projects_page.enter_project_details(identifier=project_id, name="")
        projects_page.submit_project_form()
        assert projects_page.project_count() == initial_count, "Project without a name should not be created"

        # Valid project after validation checks
        valid_project = Project(identifier=project_id, name=f"Valid {project_id}")
        projects_page.create_project(valid_project)
        projects_page.open()
        assert projects_page.project_count() == initial_count + 1, "Valid project was not created after validation retries"
    finally:
        DashboardPage(driver, xnat_config.base_url).logout()
