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

    path = "/"  # Modern XNAT shows projects on the home page

    # Updated selectors for modern XNAT UI
    _new_menu = (By.CSS_SELECTOR, "a[href='#new']")
    _create_button = (By.CSS_SELECTOR, "a[href*='add_xnat_projectData']")
    _project_identifier = (By.NAME, "xnat:projectData/ID")
    _project_name = (By.NAME, "xnat:projectData/name")
    _project_description = (By.NAME, "xnat:projectData/description")
    _save_button = (By.CSS_SELECTOR, "input[name='eventSubmit_doPerform'], input[value*='Create Project'], button[type='submit'], input[type='submit']")
    _project_table_rows = (By.CSS_SELECTOR, "table.xnat-table tbody tr[data-id]")  # Modern XNAT uses data-id attributes
    _project_row_link = "a[href*='%s']"
    _projects_menu = (By.ID, "browse-projects-menu-item")

    def open(self) -> "ProjectsPage":
        self.visit(self.path)
        # Check for presence since the menu may be hidden in a dropdown
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
        wait = WebDriverWait(self.driver, self.timeout)
        wait.until(EC.presence_of_element_located(self._projects_menu))
        return self

    def wait_until_loaded(self, *, timeout: int | None = None) -> None:
        """Wait until the project listing has fully loaded."""

        # Modern XNAT shows projects in dropdown menus on the home page
        # Check for presence since the menu may be hidden in a dropdown
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
        wait = WebDriverWait(self.driver, timeout or self.timeout)
        wait.until(EC.presence_of_element_located(self._projects_menu))

    def is_loaded(self, *, timeout: int | None = None) -> bool:
        """Return ``True`` when the project listing controls are visible."""

        try:
            self.wait_until_loaded(timeout=timeout)
            return True
        except TimeoutException:
            return False

    def start_project_creation(self) -> None:
        # In modern XNAT, project creation is under the "New" menu
        self.click(self._new_menu)
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
        # Wait for either URL change (successful creation) or stay on form (validation error)
        import time
        time.sleep(2)  # Give time for any JavaScript processing and redirect

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
