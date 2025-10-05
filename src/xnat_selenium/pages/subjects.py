"""Page object helpers for managing subjects within a project."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from selenium.webdriver.common.by import By

from .base import BasePage


@dataclass
class Subject:
    """Representation of an XNAT subject used in tests."""

    label: str
    species: Optional[str] = None


class SubjectsPage(BasePage):
    """Interact with the subject list within a project."""

    _add_subject_button = (By.CSS_SELECTOR, "a[href*='AddSubject'], button#create-subject")
    _subject_label = (By.NAME, "label")
    _subject_species = (By.NAME, "species")
    _save_subject = (By.CSS_SELECTOR, "form button[type='submit'], form input[type='submit']")
    _subject_table_rows = (By.CSS_SELECTOR, "table.subject-list tbody tr")

    def open(self, project_identifier: str) -> None:
        self.visit(f"/app/action/DisplayItemAction/search_element/subject/search_field/PROJECT/search_value/{project_identifier}")
        self.wait_for_visibility(self._add_subject_button)

    def start_subject_creation(self) -> None:
        self.click(self._add_subject_button)
        self.wait_for_visibility(self._subject_label)

    def enter_subject_details(self, *, label: str | None = None, species: str | None = None) -> None:
        if label is not None:
            self.fill(self._subject_label, label)
        if species is not None:
            self.fill(self._subject_species, species)

    def submit_subject_form(self) -> None:
        self.click(self._save_subject)

    def add_subject(self, subject: Subject) -> None:
        self.start_subject_creation()
        self.enter_subject_details(label=subject.label, species=subject.species)
        self.submit_subject_form()

    def subject_exists(self, subject: Subject) -> bool:
        rows = self.subject_rows()
        if subject.species:
            return any(subject.label in row and subject.species in row for row in rows)
        return any(subject.label in row for row in rows)

    def subject_rows(self) -> list[str]:
        """Return the raw text contents of the subject table rows."""

        return [row.text for row in self.elements(self._subject_table_rows)]

    def subject_count(self) -> int:
        """Return the number of subjects currently displayed."""

        return len(self.elements(self._subject_table_rows))
