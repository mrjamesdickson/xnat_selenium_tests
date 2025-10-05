"""Subject and experiment workflows adapted from the Bitbucket reference suite."""
from __future__ import annotations

import uuid

import pytest

from xnat_selenium.pages.dashboard import DashboardPage
from xnat_selenium.pages.experiments import Experiment, ExperimentsPage
from xnat_selenium.pages.login import LoginPage
from xnat_selenium.pages.projects import Project, ProjectsPage
from xnat_selenium.pages.subjects import Subject, SubjectsPage


def _login_to_dashboard(driver, xnat_config) -> DashboardPage:
    login_page = LoginPage(driver, xnat_config.base_url).open()
    login_page.login(xnat_config.username, xnat_config.password)
    dashboard = DashboardPage(driver, xnat_config.base_url)
    dashboard.wait_until_loaded()
    return dashboard


@pytest.mark.projects
@pytest.mark.subjects
def test_duplicate_subject_updates_species(driver, xnat_config):
    """Re-adding a subject should refresh its metadata instead of creating duplicates."""

    dashboard = _login_to_dashboard(driver, xnat_config)
    project_id = f"AUTO{uuid.uuid4().hex[:6]}"
    project = Project(identifier=project_id, name=f"Project {project_id}")
    subject_label = f"SUBJ-{uuid.uuid4().hex[:6]}"

    try:
        dashboard.go_to_projects()
        projects_page = ProjectsPage(driver, xnat_config.base_url)
        projects_page.open()
        projects_page.create_project(project)
        projects_page.open()

        subjects_page = SubjectsPage(driver, xnat_config.base_url)
        subjects_page.open(project.identifier)
        subjects_page.add_subject(Subject(label=subject_label, species="Homo sapiens"))
        subjects_page.add_subject(Subject(label=subject_label, species="Pan troglodytes"))

        rows = subjects_page.subject_rows()
        matching_rows = [row for row in rows if subject_label in row]
        assert matching_rows, "Subject did not appear in the listing"
        row_text = matching_rows[0]
        assert "Pan troglodytes" in row_text, "Updated species was not visible after re-adding subject"
        assert "Homo sapiens" not in row_text, "Stale species information remained after update"
    finally:
        DashboardPage(driver, xnat_config.base_url).logout()


@pytest.mark.projects
@pytest.mark.subjects
def test_subject_creation_requires_label(driver, xnat_config):
    """Submitting the subject form without a label should not add to the table."""

    dashboard = _login_to_dashboard(driver, xnat_config)
    project_id = f"AUTO{uuid.uuid4().hex[:6]}"
    project = Project(identifier=project_id, name=f"Project {project_id}")

    try:
        dashboard.go_to_projects()
        projects_page = ProjectsPage(driver, xnat_config.base_url)
        projects_page.open()
        projects_page.create_project(project)
        projects_page.open()

        subjects_page = SubjectsPage(driver, xnat_config.base_url)
        subjects_page.open(project.identifier)
        subjects_page.start_subject_creation()
        subjects_page.enter_subject_details(species="Homo sapiens")
        subjects_page.submit_subject_form()

        assert subjects_page.subject_count() == 0, "Subject without a label should not be persisted"
    finally:
        DashboardPage(driver, xnat_config.base_url).logout()


@pytest.mark.projects
@pytest.mark.experiments
def test_duplicate_experiment_updates_modality(driver, xnat_config):
    """Experiment metadata should be replaced when the same label is submitted twice."""

    dashboard = _login_to_dashboard(driver, xnat_config)
    project_id = f"AUTO{uuid.uuid4().hex[:6]}"
    project = Project(identifier=project_id, name=f"Project {project_id}")
    subject = Subject(label=f"SUBJ-{uuid.uuid4().hex[:6]}")
    experiment_label = f"EXP-{uuid.uuid4().hex[:6]}"

    try:
        dashboard.go_to_projects()
        projects_page = ProjectsPage(driver, xnat_config.base_url)
        projects_page.open()
        projects_page.create_project(project)
        projects_page.open()

        subjects_page = SubjectsPage(driver, xnat_config.base_url)
        subjects_page.open(project.identifier)
        subjects_page.add_subject(subject)

        experiments_page = ExperimentsPage(driver, xnat_config.base_url)
        experiments_page.open(project.identifier, subject.label)
        experiments_page.add_experiment(Experiment(label=experiment_label, modality="MR"))
        experiments_page.add_experiment(Experiment(label=experiment_label, modality="PET"))

        rows = experiments_page.experiment_rows()
        matching_rows = [row for row in rows if experiment_label in row]
        assert matching_rows, "Experiment did not appear in the listing"
        row_text = matching_rows[0]
        assert "PET" in row_text, "Updated modality was not visible after re-adding experiment"
        assert "MR" not in row_text, "Stale modality information remained after update"
    finally:
        DashboardPage(driver, xnat_config.base_url).logout()


@pytest.mark.projects
@pytest.mark.experiments
def test_experiment_creation_requires_label(driver, xnat_config):
    """Submitting the experiment form without a label should not create a session."""

    dashboard = _login_to_dashboard(driver, xnat_config)
    project_id = f"AUTO{uuid.uuid4().hex[:6]}"
    project = Project(identifier=project_id, name=f"Project {project_id}")
    subject = Subject(label=f"SUBJ-{uuid.uuid4().hex[:6]}")

    try:
        dashboard.go_to_projects()
        projects_page = ProjectsPage(driver, xnat_config.base_url)
        projects_page.open()
        projects_page.create_project(project)
        projects_page.open()

        subjects_page = SubjectsPage(driver, xnat_config.base_url)
        subjects_page.open(project.identifier)
        subjects_page.add_subject(subject)

        experiments_page = ExperimentsPage(driver, xnat_config.base_url)
        experiments_page.open(project.identifier, subject.label)
        experiments_page.start_experiment_creation()
        experiments_page.enter_experiment_details(modality="CT")
        experiments_page.submit_experiment_form()

        assert experiments_page.experiment_count() == 0, "Experiment without a label should not be persisted"
    finally:
        DashboardPage(driver, xnat_config.base_url).logout()
