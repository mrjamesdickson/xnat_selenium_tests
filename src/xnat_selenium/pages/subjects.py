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

    def add_subject(self, subject: Subject) -> None:
        self.click(self._add_subject_button)
        self.wait_for_visibility(self._subject_label)
        self.fill(self._subject_label, subject.label)
        if subject.species:
            self.fill(self._subject_species, subject.species)
        self.click(self._save_subject)

    def subject_exists(self, subject: Subject) -> bool:
        rows = self.elements(self._subject_table_rows)
        return any(subject.label in row.text for row in rows)
