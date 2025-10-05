"""Page objects related to project management in XNAT."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from selenium.webdriver.common.by import By

from .base import BasePage


@dataclass
class Project:
    """Simple representation of an XNAT project used in tests."""

    identifier: str
    name: str
    description: Optional[str] = None


class ProjectsPage(BasePage):
    """Interact with the project listing and creation screens."""

    path = "/app/template/XDATScreen_manage_projects.vm"

    _create_button = (By.CSS_SELECTOR, "a#create-project, a[href*='CreateProject']")
    _project_identifier = (By.NAME, "ID")
    _project_name = (By.NAME, "name")
    _project_description = (By.NAME, "description")
    _save_button = (By.CSS_SELECTOR, "form button[type='submit'], form input[type='submit']")
    _project_table_rows = (By.CSS_SELECTOR, "table.project-list tbody tr")
    _project_row_link = "a[href*='projectID=%s']"

    def open(self) -> "ProjectsPage":
        self.visit(self.path)
        self.wait_for_visibility(self._create_button)
        return self

    def start_project_creation(self) -> None:
        self.click(self._create_button)
        self.wait_for_visibility(self._project_identifier)

    def create_project(self, project: Project) -> None:
        self.start_project_creation()
        self.fill(self._project_identifier, project.identifier)
        self.fill(self._project_name, project.name)
        if project.description:
            self.fill(self._project_description, project.description)
        self.click(self._save_button)

    def project_exists(self, project: Project) -> bool:
        rows = self.elements(self._project_table_rows)
        return any(project.identifier in row.text for row in rows)

    def open_project(self, project: Project) -> None:
        link = (By.CSS_SELECTOR, self._project_row_link % project.identifier)
        self.click(link)
