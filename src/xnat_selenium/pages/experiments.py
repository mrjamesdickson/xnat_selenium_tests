"""Page object helpers for managing imaging sessions (experiments)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from selenium.webdriver.common.by import By

from .base import BasePage


@dataclass
class Experiment:
    """Representation of an XNAT experiment (imaging session)."""

    label: str
    modality: Optional[str] = None


class ExperimentsPage(BasePage):
    """Interact with experiments for a given subject."""

    _add_experiment_button = (By.CSS_SELECTOR, "a[href*='AddExperiment'], button#create-session")
    _experiment_label = (By.NAME, "label")
    _experiment_modality = (By.NAME, "modality")
    _save_button = (By.CSS_SELECTOR, "form button[type='submit'], form input[type='submit']")
    _experiment_table_rows = (By.CSS_SELECTOR, "table.experiment-list tbody tr")

    def open(self, project_identifier: str, subject_label: str) -> None:
        self.visit(
            f"/app/action/DisplayItemAction/search_element/experiment/search_field/PROJECT/search_value/{project_identifier}?subject={subject_label}"
        )
        self.wait_for_visibility(self._add_experiment_button)

    def add_experiment(self, experiment: Experiment) -> None:
        self.click(self._add_experiment_button)
        self.wait_for_visibility(self._experiment_label)
        self.fill(self._experiment_label, experiment.label)
        if experiment.modality:
            self.fill(self._experiment_modality, experiment.modality)
        self.click(self._save_button)

    def experiment_exists(self, experiment: Experiment) -> bool:
        rows = self.elements(self._experiment_table_rows)
        return any(experiment.label in row.text for row in rows)
