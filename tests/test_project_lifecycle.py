"""End-to-end project lifecycle coverage."""
from __future__ import annotations

import uuid

import pytest

from xnat_selenium.pages.dashboard import DashboardPage
from xnat_selenium.pages.experiments import Experiment, ExperimentsPage
from xnat_selenium.pages.login import LoginPage
from xnat_selenium.pages.projects import Project, ProjectsPage
from xnat_selenium.pages.subjects import Subject, SubjectsPage


@pytest.mark.e2e
@pytest.mark.projects
def test_project_subject_and_experiment_creation(driver, xnat_config):
    """Create a project, add a subject, and register an experiment."""
    identifier = f"AUTO{uuid.uuid4().hex[:6]}"
    project = Project(identifier=identifier, name=f"Automated Project {identifier}", description="Created by Selenium tests")
    subject = Subject(label=f"SUBJ-{uuid.uuid4().hex[:6]}")
    experiment = Experiment(label=f"EXP-{uuid.uuid4().hex[:6]}")

    login_page = LoginPage(driver, xnat_config.base_url).open()
    login_page.login(xnat_config.username, xnat_config.password)
    dashboard = DashboardPage(driver, xnat_config.base_url)
    dashboard.wait_until_loaded()

    try:
        dashboard.go_to_projects()

        projects_page = ProjectsPage(driver, xnat_config.base_url)
        projects_page.open()
        projects_page.create_project(project)

        projects_page.open()
        projects_page.wait_until(lambda drv: projects_page.project_exists(project), message="project to appear in table")

        subjects_page = SubjectsPage(driver, xnat_config.base_url)
        subjects_page.open(project.identifier)
        subjects_page.add_subject(subject)
        subjects_page.wait_until(lambda drv: subjects_page.subject_exists(subject), message="subject to appear in table")

        experiments_page = ExperimentsPage(driver, xnat_config.base_url)
        experiments_page.open(project.identifier, subject.label)
        experiments_page.add_experiment(experiment)
        experiments_page.wait_until(
            lambda drv: experiments_page.experiment_exists(experiment), message="experiment to appear in table"
        )
    finally:
        DashboardPage(driver, xnat_config.base_url).logout()


@pytest.mark.e2e
@pytest.mark.projects
def test_project_with_subject_species_and_experiment_modality(driver, xnat_config):
    """Optional subject and experiment fields should be persisted."""

    identifier = f"AUTO{uuid.uuid4().hex[:6]}"
    project = Project(identifier=identifier, name=f"Optional Fields {identifier}")
    subject = Subject(label=f"SUBJ-{uuid.uuid4().hex[:6]}", species="Homo sapiens")
    experiment = Experiment(label=f"EXP-{uuid.uuid4().hex[:6]}", modality="MR")

    login_page = LoginPage(driver, xnat_config.base_url).open()
    login_page.login(xnat_config.username, xnat_config.password)
    dashboard = DashboardPage(driver, xnat_config.base_url)
    dashboard.wait_until_loaded()

    try:
        dashboard.go_to_projects()

        projects_page = ProjectsPage(driver, xnat_config.base_url)
        projects_page.open()
        projects_page.create_project(project)
        projects_page.open()
        projects_page.wait_until(lambda drv: projects_page.project_exists(project), message="project to appear in table")

        subjects_page = SubjectsPage(driver, xnat_config.base_url)
        subjects_page.open(project.identifier)
        subjects_page.add_subject(subject)
        subjects_page.wait_until(lambda drv: subjects_page.subject_exists(subject), message="subject to appear in table")

        experiments_page = ExperimentsPage(driver, xnat_config.base_url)
        experiments_page.open(project.identifier, subject.label)
        experiments_page.add_experiment(experiment)
        experiments_page.wait_until(
            lambda drv: experiments_page.experiment_exists(experiment), message="experiment to appear in table"
        )
    finally:
        DashboardPage(driver, xnat_config.base_url).logout()
