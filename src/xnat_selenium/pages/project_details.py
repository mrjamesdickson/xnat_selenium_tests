"""Project details tab helpers inspired by the legacy Selenium suite."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .projects import Project


@dataclass(frozen=True)
class ProjectSnapshot:
    """Lightweight container mirroring the fields shown on the details tab."""

    identifier: str
    description: str | None = None
    aliases: Sequence[str] = ()
    keywords: Sequence[str] = ()

    @classmethod
    def from_project(cls, project: Project) -> "ProjectSnapshot":
        return cls(
            identifier=project.identifier,
            description=project.description,
            aliases=project.aliases,
            keywords=project.keywords,
        )


class ProjectDetailsTab:
    """Default behaviour for recent XNAT versions."""

    def escape_on_project_page(self, text: str) -> str:
        return text

    def expected_project_id_string(self, project: ProjectSnapshot | Project) -> str:
        snapshot = self._snapshot(project)
        alias_blob = " ".join(snapshot.aliases)
        if alias_blob:
            escaped = self.escape_on_project_page(alias_blob)
            return f"{snapshot.identifier} Aka: {escaped}"
        return snapshot.identifier

    def render_description(self, project: ProjectSnapshot | Project) -> str | None:
        snapshot = self._snapshot(project)
        if snapshot.description is None:
            return None
        return self.escape_on_project_page(snapshot.description)

    def render_keywords(self, project: ProjectSnapshot | Project) -> str:
        snapshot = self._snapshot(project)
        if not snapshot.keywords:
            return ""
        blob = " ".join(snapshot.keywords)
        return self.escape_on_project_page(blob)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _snapshot(self, project: ProjectSnapshot | Project) -> ProjectSnapshot:
        if isinstance(project, ProjectSnapshot):
            return project
        return ProjectSnapshot.from_project(project)


class LegacyProjectDetailsTab(ProjectDetailsTab):
    """Historic behaviour that performed HTML escaping on display."""

    _ESCAPE_MAP = {
        "&": "&amp",
        "<": "&lt",
        ">": "&gt",
        "'": "&apos",
    }

    def escape_on_project_page(self, text: str) -> str:
        escaped = text
        for needle, replacement in self._ESCAPE_MAP.items():
            escaped = escaped.replace(needle, replacement)
        return escaped
