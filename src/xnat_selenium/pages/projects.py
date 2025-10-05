"""Page objects related to project management in XNAT."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from .base import BasePage


@dataclass
class Project:
    """Simple representation of an XNAT project used in tests."""

    identifier: str
    name: str
    description: Optional[str] = None
    aliases: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        # Normalise potentially mutable iterables passed by callers so that
        # repeated access always yields immutable tuples.  The production XNAT
        # UI stores aliases and keywords as lists, so allowing callers to pass
        # either lists or tuples keeps the tests ergonomic.
        if not isinstance(self.aliases, tuple):
            self.aliases = tuple(self.aliases or ())
        if not isinstance(self.keywords, tuple):
            self.keywords = tuple(self.keywords or ())


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

    def wait_until_loaded(self, *, timeout: int | None = None) -> None:
        """Wait until the project listing has fully loaded."""

        self.wait_for_visibility(self._create_button, timeout=timeout)

    def is_loaded(self, *, timeout: int | None = None) -> bool:
        """Return ``True`` when the project listing controls are visible."""

        try:
            self.wait_until_loaded(timeout=timeout)
            return True
        except TimeoutException:
            return False

    def start_project_creation(self) -> None:
        self.click(self._create_button)
        self.wait_for_visibility(self._project_identifier)

    def enter_project_details(
        self,
        *,
        identifier: str | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        """Populate the project creation form fields."""

        if identifier is not None:
            self.fill(self._project_identifier, identifier)
        if name is not None:
            self.fill(self._project_name, name)
        if description is not None:
            self.fill(self._project_description, description)

    def submit_project_form(self) -> None:
        """Submit the project creation form without additional validation."""

        self.click(self._save_button)

    def create_project(self, project: Project) -> None:
        self.start_project_creation()
        self.enter_project_details(identifier=project.identifier, name=project.name, description=project.description)
        self.submit_project_form()

    def project_exists(self, project: Project) -> bool:
        rows = self.project_rows()
        if project.description:
            return any(project.identifier in row and project.description in row for row in rows)
        return any(project.identifier in row for row in rows)

    def project_rows(self) -> list[str]:
        """Return the raw text contents of the project table rows."""

        return [row.text for row in self.elements(self._project_table_rows)]

    def project_count(self) -> int:
        """Return the number of projects currently displayed."""

        return len(self.elements(self._project_table_rows))

    def open_project(self, project: Project) -> None:
        link = (By.CSS_SELECTOR, self._project_row_link % project.identifier)
        self.click(link)
