"""Unit tests mirroring legacy behaviours from the Bitbucket suite."""
from __future__ import annotations

import pytest

from xnat_selenium.pages.project_details import LegacyProjectDetailsTab, ProjectDetailsTab
from xnat_selenium.pages.projects import Project


@pytest.mark.projects
@pytest.mark.parametrize(
    "tab_cls, expected",
    [
        (ProjectDetailsTab, "Functional & Research"),
        (LegacyProjectDetailsTab, "Functional &amp Research"),
    ],
)
def test_escape_on_project_page_matches_version_behaviour(tab_cls, expected):
    """Legacy versions escaped HTML entities while modern builds do not."""

    tab = tab_cls()
    assert tab.escape_on_project_page("Functional & Research") == expected


@pytest.mark.projects
@pytest.mark.parametrize(
    "tab_cls, aliases, expected",
    [
        (ProjectDetailsTab, ("XG 001",), "XG001 Aka: XG 001"),
        (LegacyProjectDetailsTab, ("XG & 001",), "XG001 Aka: XG &amp 001"),
    ],
)
def test_expected_project_id_string_includes_aliases(tab_cls, aliases, expected):
    project = Project(identifier="XG001", name="XNAT Growth", aliases=aliases)
    tab = tab_cls()
    assert tab.expected_project_id_string(project) == expected


@pytest.mark.projects
@pytest.mark.parametrize("tab_cls", [ProjectDetailsTab, LegacyProjectDetailsTab])
def test_render_helpers_respect_escape_strategy(tab_cls):
    description = "Detailed <overview> & planning"
    keywords = ("longitudinal", "analysis & planning")
    project = Project(
        identifier="XG002",
        name="Secondary",
        description=description,
        keywords=keywords,
    )

    tab = tab_cls()
    rendered_description = tab.render_description(project)
    rendered_keywords = tab.render_keywords(project)

    if tab_cls is LegacyProjectDetailsTab:
        assert rendered_description == "Detailed &ltoverview&gt &amp planning"
        assert rendered_keywords == "longitudinal analysis &amp planning"
    else:
        assert rendered_description == description
        assert rendered_keywords == "longitudinal analysis & planning"


@pytest.mark.projects
@pytest.mark.parametrize("tab_cls", [ProjectDetailsTab, LegacyProjectDetailsTab])
def test_render_helpers_handle_missing_data(tab_cls):
    project = Project(identifier="XG003", name="Tertiary")
    tab = tab_cls()
    assert tab.render_description(project) is None
    assert tab.render_keywords(project) == ""
