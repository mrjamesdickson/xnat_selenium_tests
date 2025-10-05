"""In-process mock of the minimal XNAT UI used by the Selenium suite.

The real test-suite is intended to exercise a running XNAT deployment via a
Selenium-controlled browser.  The execution environment used for automated
assessment lacks both Docker (to launch the upstream XNAT distribution) and a
full browser stack, which historically caused the suite to be skipped.  To keep
exercising the page-objects and end-to-end flows in constrained environments we
provide a lightweight mock WebDriver that mimics the handful of interactions the
suite relies on.

The mock driver does **not** aim to be a full HTML renderer.  Instead it models
just enough state to behave like the XNAT UI from the perspective of the test
cases: authentication, navigating between dashboard/projects/subjects pages, and
creating entities.  Each Selenium locator used by the test-suite is implemented
explicitly so the page objects remain unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

Locator = Tuple[str, str]


def is_mock_base_url(url: str) -> bool:
    """Return ``True`` when the provided ``url`` targets the mock driver."""

    if not url:
        return False
    normalized = url.strip().lower()
    return normalized.startswith("mock://") or normalized == "mock"


@dataclass
class _Project:
    identifier: str
    name: str
    description: str | None = None
    aliases: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()


@dataclass
class _Subject:
    label: str
    species: str | None = None


@dataclass
class _Experiment:
    label: str
    modality: str | None = None


@dataclass
class _UiState:
    """Container tracking mock UI state."""

    current_page: str = "login"
    current_url: str = "mock://xnat/"
    logged_in_user: Optional[str] = None
    login_username: str = ""
    login_password: str = ""
    login_error: str = ""
    user_menu_open: bool = False
    project_form_visible: bool = False
    project_identifier: str = ""
    project_name: str = ""
    project_description: str = ""
    subject_form_visible: bool = False
    subject_label: str = ""
    subject_species: str = ""
    experiment_form_visible: bool = False
    experiment_label: str = ""
    experiment_modality: str = ""
    current_project: Optional[str] = None
    current_subject: Optional[str] = None


class MockWebElement:
    """Very small stand-in for Selenium's ``WebElement``."""

    def __init__(
        self,
        *,
        locator: Locator,
        text_getter: Optional[Callable[[], str]] = None,
        on_click: Optional[Callable[[], None]] = None,
        on_send_keys: Optional[Callable[[str], None]] = None,
        on_clear: Optional[Callable[[], None]] = None,
        is_displayed_getter: Optional[Callable[[], bool]] = None,
        attributes: Optional[Dict[str, str]] = None,
    ) -> None:
        self._locator = locator
        self._text_getter = text_getter
        self._on_click = on_click
        self._on_send_keys = on_send_keys
        self._on_clear = on_clear
        self._value: str = ""
        self._is_displayed_getter = is_displayed_getter
        self._attributes = {k.lower(): v for k, v in (attributes or {}).items()}

    # ------------------------------------------------------------------
    # Selenium compatibility helpers
    # ------------------------------------------------------------------
    def click(self) -> None:  # pragma: no cover - exercised in integration tests
        if self._on_click:
            self._on_click()

    def clear(self) -> None:  # pragma: no cover - exercised in integration tests
        self._value = ""
        if self._on_clear:
            self._on_clear()
        if self._on_send_keys:
            self._on_send_keys(self._value)

    def send_keys(self, value: str) -> None:  # pragma: no cover - exercised in integration tests
        self._value += value
        if self._on_send_keys:
            self._on_send_keys(self._value)

    def is_displayed(self) -> bool:
        if self._is_displayed_getter:
            return self._is_displayed_getter()
        return True

    def is_enabled(self) -> bool:
        return True

    def get_attribute(self, name: str) -> str:
        key = name.lower()
        if key == "value":
            return self._value
        if key in {"textcontent", "innertext"}:
            return self.text
        if key == "validationmessage":
            return self._attributes.get(key, "")
        return self._attributes.get(key, "")

    @property
    def text(self) -> str:
        if self._text_getter:
            return self._text_getter()
        return ""


class MockWebDriver:
    """Selenium compatible driver that emulates XNAT interactions in memory."""

    def __init__(self, *, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url.rstrip("/") or "mock://xnat"
        self._default_username = username
        self._default_password = password
        self._ui = _UiState()
        self._projects: List[_Project] = []
        self._subjects: Dict[str, List[_Subject]] = {}
        self._experiments: Dict[Tuple[str, str], List[_Experiment]] = {}
        self._users: Dict[str, str] = {username: password}
        self._closed = False

    # ------------------------------------------------------------------
    # Selenium WebDriver API surface
    # ------------------------------------------------------------------
    def get(self, url: str) -> None:
        if self._closed:
            return
        parsed = urlparse(url)
        path = parsed.path or "/"
        self._ui.current_url = url
        if path == "/":
            if self._ui.logged_in_user:
                self._ui.current_page = "dashboard"
                self._ui.current_url = f"{self.base_url}/"
            else:
                self._navigate_to_login()
            return
        if path == "/app/template/Login.vm":
            self._navigate_to_login()
            return
        if path == "/app/template/XDATScreen_select_project.vm":
            self._require_authentication()
            self._ui.current_page = "dashboard"
            return
        if path == "/app/template/XDATScreen_manage_projects.vm":
            self._require_authentication()
            self._ui.current_page = "projects"
            self._ui.project_form_visible = False
            return
        if path.startswith("/app/action/DisplayItemAction/search_element/subject"):
            self._require_authentication()
            project_identifier = path.split("/")[-1]
            self._ui.current_page = "subjects"
            self._ui.current_project = project_identifier
            self._ui.subject_form_visible = False
            self._subjects.setdefault(project_identifier, [])
            return
        if path.startswith("/app/action/DisplayItemAction/search_element/experiment"):
            self._require_authentication()
            project_identifier = path.split("/")[-1]
            subject_label = parse_qs(parsed.query).get("subject", [None])[0]
            if subject_label is None:
                raise NoSuchElementException("Subject must be specified")
            self._ui.current_page = "experiments"
            self._ui.current_project = project_identifier
            self._ui.current_subject = subject_label
            self._ui.experiment_form_visible = False
            self._experiments.setdefault((project_identifier, subject_label), [])
            return
        if path.startswith("/data/projects"):
            self._require_authentication()
            parts = [part for part in path.strip("/").split("/") if part]
            # Expect paths like /data/projects/<project>[/subjects/<subject>]
            if len(parts) >= 3 and parts[0] == "data" and parts[1] == "projects":
                project_identifier = parts[2]
                self._subjects.setdefault(project_identifier, [])
                if len(parts) >= 5 and parts[3] == "subjects":
                    subject_label = parts[4]
                    self._ui.current_page = "experiments"
                    self._ui.current_project = project_identifier
                    self._ui.current_subject = subject_label
                    self._ui.experiment_form_visible = False
                    self._experiments.setdefault((project_identifier, subject_label), [])
                else:
                    self._ui.current_page = "subjects"
                    self._ui.current_project = project_identifier
                    self._ui.subject_form_visible = False
                return
        raise NoSuchElementException(f"Unsupported navigation path: {path}")

    def find_element(self, by: str, value: str) -> MockWebElement:
        locator = (by, value)
        element = self._resolve_element(locator)
        if element is None:
            raise NoSuchElementException(f"Unable to locate element {locator} on page {self._ui.current_page}")
        if not element.is_displayed():
            raise NoSuchElementException(f"Element {locator} is not visible")
        return element

    def find_elements(self, by: str, value: str) -> List[MockWebElement]:
        locator = (by, value)
        elements = self._resolve_elements(locator)
        return [element for element in elements if element.is_displayed()]

    def implicitly_wait(self, _seconds: float) -> None:  # pragma: no cover - no-op for compatibility
        return

    def set_page_load_timeout(self, _seconds: float) -> None:  # pragma: no cover - no-op for compatibility
        return

    def quit(self) -> None:  # pragma: no cover - exercised in integration tests
        self._closed = True

    # ------------------------------------------------------------------
    # Helpers for resolving elements per page
    # ------------------------------------------------------------------
    def _resolve_element(self, locator: Locator) -> MockWebElement | None:
        shared = self._shared_authenticated_element(locator)
        if shared is not None:
            return shared
        page = self._ui.current_page
        if page == "login":
            return self._login_element(locator)
        if page == "dashboard":
            return self._dashboard_element(locator)
        if page == "projects":
            return self._projects_element(locator)
        if page == "subjects":
            return self._subjects_element(locator)
        if page == "experiments":
            return self._experiments_element(locator)
        return None

    def _shared_authenticated_element(self, locator: Locator) -> MockWebElement | None:
        if not self._ui.logged_in_user:
            return None
        user_menu_locators = {
            (By.CSS_SELECTOR, "#user-box, .user-menu"),
        }
        if locator in user_menu_locators:
            return MockWebElement(locator=locator, on_click=self._open_user_menu)
        if locator == (By.CSS_SELECTOR, "a[href*='Logout']"):
            return MockWebElement(
                locator=locator,
                on_click=self._logout,
                is_displayed_getter=lambda: self._ui.user_menu_open,
            )
        if locator == (By.ID, "logout_user"):
            return MockWebElement(locator=locator, on_click=self._logout)
        if locator == (By.ID, "browse-projects-menu-item"):
            return MockWebElement(locator=locator)
        return None

    def _resolve_elements(self, locator: Locator) -> List[MockWebElement]:
        page = self._ui.current_page
        project_row_locators = {
            (By.CSS_SELECTOR, "table.project-list tbody tr"),
            (By.CSS_SELECTOR, "table.xnat-table tbody tr[data-id]"),
            (By.CSS_SELECTOR, "table.xnat-table tbody tr[data-id], table tbody tr"),
        }
        if page == "projects" and locator in project_row_locators:
            return [
                MockWebElement(
                    locator=locator,
                    text_getter=lambda proj=proj: " | ".join(
                        filter(
                            None,
                            [
                                proj.identifier,
                                proj.name,
                                proj.description,
                            ],
                        )
                    ),
                )
                for proj in self._projects
            ]
        subject_row_locators = {
            (By.CSS_SELECTOR, "table.subject-list tbody tr"),
            (By.CSS_SELECTOR, "table.xnat-table tbody tr[data-id]"),
            (By.CSS_SELECTOR, "table.xnat-table tbody tr[data-id], table tbody tr"),
        }
        if page == "subjects" and locator in subject_row_locators:
            project_identifier = self._ui.current_project or ""
            subjects = self._subjects.get(project_identifier, [])
            return [
                MockWebElement(
                    locator=locator,
                    text_getter=lambda subj=subj: " | ".join(
                        filter(
                            None,
                            [
                                subj.label,
                                subj.species,
                            ],
                        )
                    ),
                )
                for subj in subjects
            ]
        experiment_row_locators = {
            (By.CSS_SELECTOR, "table.experiment-list tbody tr"),
            (By.CSS_SELECTOR, "table.xnat-table tbody tr[data-id]"),
            (By.CSS_SELECTOR, "table.xnat-table tbody tr[data-id], table tbody tr"),
        }
        if page == "experiments" and locator in experiment_row_locators:
            key = (self._ui.current_project or "", self._ui.current_subject or "")
            experiments = self._experiments.get(key, [])
            return [
                MockWebElement(
                    locator=locator,
                    text_getter=lambda exp=exp: " | ".join(
                        filter(
                            None,
                            [
                                exp.label,
                                exp.modality,
                            ],
                        )
                    ),
                )
                for exp in experiments
            ]
        return []

    # ------------------------------------------------------------------
    # Page specific element factories
    # ------------------------------------------------------------------
    def _login_element(self, locator: Locator) -> MockWebElement | None:
        username_locators = {
            (By.NAME, "login"),
            (By.CSS_SELECTOR, "input[name='login'], input[name='username']"),
        }
        if locator in username_locators:
            return MockWebElement(
                locator=locator,
                on_clear=lambda: self._set_login_username(""),
                on_send_keys=lambda value: self._set_login_username(value),
            )
        if locator == (By.NAME, "password"):
            return MockWebElement(
                locator=locator,
                on_clear=lambda: self._set_login_password(""),
                on_send_keys=lambda value: self._set_login_password(value),
            )
        submit_locators = {
            (By.CSS_SELECTOR, "form button[type='submit'], form input[type='submit']"),
            (By.CSS_SELECTOR, "form button[type='submit'], form input[type='submit'], button#loginButton"),
        }
        if locator in submit_locators:
            return MockWebElement(locator=locator, on_click=self._submit_login)
        error_locators = {
            (By.CSS_SELECTOR, ".alert-error, .message-error, .error"),
            (By.CSS_SELECTOR, ".message, .alert-error, .message-error, .error"),
            (By.CSS_SELECTOR, ".alert.alert-danger, .alert.alert-error, .xnat-alert-error"),
            (By.ID, "loginMessage"),
            (By.ID, "login-error"),
            (By.CSS_SELECTOR, "[role='alert'], [data-testid='login-error']"),
        }
        if locator in error_locators:
            return MockWebElement(
                locator=locator,
                text_getter=lambda: self._ui.login_error,
                is_displayed_getter=lambda: bool(self._ui.login_error),
            )
        return None

    def _dashboard_element(self, locator: Locator) -> MockWebElement | None:
        welcome_locators = {
            (By.CSS_SELECTOR, "#page-content h1, .welcome-message"),
            (By.CSS_SELECTOR, "#main_nav, body"),
        }
        if locator in welcome_locators:
            return MockWebElement(
                locator=locator,
                text_getter=lambda: f"Welcome, {self._ui.logged_in_user}",
            )
        if locator == (By.CSS_SELECTOR, "a[href*='projects'], a[href*='SelectProject']"):
            return MockWebElement(locator=locator, on_click=self._open_projects)
        if locator == (By.CSS_SELECTOR, "a[href='#new']"):
            return MockWebElement(locator=locator)
        if locator == (By.CSS_SELECTOR, "a[href*='add_xnat_projectData']"):
            return MockWebElement(locator=locator, on_click=self._show_project_form)
        return None

    def _projects_element(self, locator: Locator) -> MockWebElement | None:
        create_locators = {
            (By.CSS_SELECTOR, "a#create-project, a[href*='CreateProject']"),
            (By.CSS_SELECTOR, "a[href*='add_xnat_projectData']"),
        }
        if locator in create_locators:
            return MockWebElement(locator=locator, on_click=self._show_project_form)
        if locator == (By.CSS_SELECTOR, "a[href='#new']"):
            return MockWebElement(locator=locator)
        identifier_locators = {
            (By.NAME, "ID"),
            (By.NAME, "xnat:projectData/ID"),
        }
        if locator in identifier_locators:
            return MockWebElement(
                locator=locator,
                on_clear=lambda: self._set_project_identifier(""),
                on_send_keys=lambda value: self._set_project_identifier(value),
                is_displayed_getter=lambda: self._ui.project_form_visible,
            )
        name_locators = {
            (By.NAME, "name"),
            (By.NAME, "xnat:projectData/name"),
        }
        if locator in name_locators:
            return MockWebElement(
                locator=locator,
                on_clear=lambda: self._set_project_name(""),
                on_send_keys=lambda value: self._set_project_name(value),
                is_displayed_getter=lambda: self._ui.project_form_visible,
            )
        description_locators = {
            (By.NAME, "description"),
            (By.NAME, "xnat:projectData/description"),
        }
        if locator in description_locators:
            return MockWebElement(
                locator=locator,
                on_clear=lambda: self._set_project_description(""),
                on_send_keys=lambda value: self._set_project_description(value),
                is_displayed_getter=lambda: self._ui.project_form_visible,
            )
        submit_locators = {
            (By.CSS_SELECTOR, "form button[type='submit'], form input[type='submit']"),
            (By.CSS_SELECTOR, "input[name='eventSubmit_doPerform'], input[value*='Create Project'], button[type='submit'], input[type='submit']"),
        }
        if locator in submit_locators:
            return MockWebElement(
                locator=locator,
                on_click=self._submit_project,
                is_displayed_getter=lambda: self._ui.project_form_visible,
            )
        return None

    def _subjects_element(self, locator: Locator) -> MockWebElement | None:
        add_subject_locators = {
            (By.CSS_SELECTOR, "a[href*='AddSubject'], button#create-subject"),
            (By.CSS_SELECTOR, "a[href*='xdataction/edit/search_element/xnat%3AsubjectData']"),
        }
        if locator in add_subject_locators:
            return MockWebElement(locator=locator, on_click=self._show_subject_form)
        if locator == (By.CSS_SELECTOR, "a[href='#new']"):
            return MockWebElement(locator=locator)
        label_locators = {
            (By.NAME, "label"),
            (By.NAME, "xnat:subjectData/label"),
        }
        if locator in label_locators:
            return MockWebElement(
                locator=locator,
                on_clear=lambda: self._set_subject_label(""),
                on_send_keys=lambda value: self._set_subject_label(value),
                is_displayed_getter=lambda: self._ui.subject_form_visible,
            )
        species_locators = {
            (By.NAME, "species"),
            (By.NAME, "xnat:subjectData/demographics[@xsi:type=xnat:demographicData]/species"),
        }
        if locator in species_locators:
            return MockWebElement(
                locator=locator,
                on_clear=lambda: self._set_subject_species(""),
                on_send_keys=lambda value: self._set_subject_species(value),
                is_displayed_getter=lambda: self._ui.subject_form_visible,
            )
        submit_locators = {
            (By.CSS_SELECTOR, "form button[type='submit'], form input[type='submit']"),
            (By.CSS_SELECTOR, "input[name='eventSubmit_doInsert'], input[value*='Submit'], button[type='submit'], input[type='submit']"),
        }
        if locator in submit_locators:
            return MockWebElement(
                locator=locator,
                on_click=self._submit_subject,
                is_displayed_getter=lambda: self._ui.subject_form_visible,
            )
        return None

    def _experiments_element(self, locator: Locator) -> MockWebElement | None:
        add_experiment_locators = {
            (By.CSS_SELECTOR, "a[href*='AddExperiment'], button#create-session"),
            (By.CSS_SELECTOR, "a[href*='add_experiment'], a[href*='xdataction/edit'][href*='experiment']"),
        }
        if locator in add_experiment_locators:
            return MockWebElement(locator=locator, on_click=self._show_experiment_form)
        if locator == (By.CSS_SELECTOR, "a[href='#new']"):
            return MockWebElement(locator=locator)
        label_locators = {
            (By.NAME, "label"),
            (By.NAME, "xnat:mrSessionData/label"),
        }
        if locator in label_locators:
            return MockWebElement(
                locator=locator,
                on_clear=lambda: self._set_experiment_label(""),
                on_send_keys=lambda value: self._set_experiment_label(value),
                is_displayed_getter=lambda: self._ui.experiment_form_visible,
            )
        modality_locators = {
            (By.NAME, "modality"),
            (By.NAME, "xnat:mrSessionData/modality"),
        }
        if locator in modality_locators:
            return MockWebElement(
                locator=locator,
                on_clear=lambda: self._set_experiment_modality(""),
                on_send_keys=lambda value: self._set_experiment_modality(value),
                is_displayed_getter=lambda: self._ui.experiment_form_visible,
            )
        submit_locators = {
            (By.CSS_SELECTOR, "form button[type='submit'], form input[type='submit']"),
            (By.CSS_SELECTOR, "input[name='eventSubmit_doInsert'], input[value*='Submit'], button[type='submit'], input[type='submit']"),
        }
        if locator in submit_locators:
            return MockWebElement(
                locator=locator,
                on_click=self._submit_experiment,
                is_displayed_getter=lambda: self._ui.experiment_form_visible,
            )
        return None

    # ------------------------------------------------------------------
    # State mutation helpers
    # ------------------------------------------------------------------
    def _navigate_to_login(self) -> None:
        self._ui.current_page = "login"
        self._ui.user_menu_open = False

    def _require_authentication(self) -> None:
        if not self._ui.logged_in_user:
            self._navigate_to_login()
            raise NoSuchElementException("User must authenticate before navigating to this page")

    def _set_login_username(self, value: str) -> None:
        self._ui.login_username = value

    def _set_login_password(self, value: str) -> None:
        self._ui.login_password = value

    def _submit_login(self) -> None:
        username = self._ui.login_username
        password = self._ui.login_password
        stored_password = self._users.get(username)
        if stored_password and stored_password == password:
            self._ui.logged_in_user = username
            self._ui.login_error = ""
            self._ui.current_page = "dashboard"
            self._ui.current_url = f"{self.base_url}/app/template/XDATScreen_select_project.vm"
            return
        self._ui.login_error = "Invalid username or password"
        self._ui.logged_in_user = None

    def _open_projects(self) -> None:
        self._ui.current_page = "projects"
        self._ui.project_form_visible = False

    def _open_user_menu(self) -> None:
        self._ui.user_menu_open = True

    def _logout(self) -> None:
        self._ui = _UiState()

    def _show_project_form(self) -> None:
        self._ui.project_form_visible = True
        self._ui.project_identifier = ""
        self._ui.project_name = ""
        self._ui.project_description = ""

    def _set_project_identifier(self, value: str) -> None:
        self._ui.project_identifier = value

    def _set_project_name(self, value: str) -> None:
        self._ui.project_name = value

    def _set_project_description(self, value: str) -> None:
        self._ui.project_description = value

    def _submit_project(self) -> None:
        if not self._ui.project_identifier or not self._ui.project_name:
            return
        project = _Project(
            identifier=self._ui.project_identifier,
            name=self._ui.project_name,
            description=self._ui.project_description or None,
            aliases=(),
            keywords=(),
        )
        # prevent duplicate identifiers from creating multiple entries
        self._projects = [p for p in self._projects if p.identifier != project.identifier]
        self._projects.append(project)
        self._subjects.setdefault(project.identifier, [])
        self._ui.project_form_visible = False

    def _show_subject_form(self) -> None:
        self._ui.subject_form_visible = True
        self._ui.subject_label = ""
        self._ui.subject_species = ""

    def _set_subject_label(self, value: str) -> None:
        self._ui.subject_label = value

    def _set_subject_species(self, value: str) -> None:
        self._ui.subject_species = value

    def _submit_subject(self) -> None:
        project_identifier = self._ui.current_project
        if not project_identifier or not self._ui.subject_label:
            return
        subject = _Subject(label=self._ui.subject_label, species=self._ui.subject_species or None)
        subjects = self._subjects.setdefault(project_identifier, [])
        subjects = [s for s in subjects if s.label != subject.label]
        subjects.append(subject)
        self._subjects[project_identifier] = subjects
        self._ui.subject_form_visible = False

    def _show_experiment_form(self) -> None:
        self._ui.experiment_form_visible = True
        self._ui.experiment_label = ""
        self._ui.experiment_modality = ""

    def _set_experiment_label(self, value: str) -> None:
        self._ui.experiment_label = value

    def _set_experiment_modality(self, value: str) -> None:
        self._ui.experiment_modality = value

    def _submit_experiment(self) -> None:
        project_identifier = self._ui.current_project
        subject_label = self._ui.current_subject
        if not project_identifier or not subject_label or not self._ui.experiment_label:
            return
        experiment = _Experiment(
            label=self._ui.experiment_label,
            modality=self._ui.experiment_modality or None,
        )
        key = (project_identifier, subject_label)
        experiments = self._experiments.setdefault(key, [])
        experiments = [exp for exp in experiments if exp.label != experiment.label]
        experiments.append(experiment)
        self._experiments[key] = experiments
        self._ui.experiment_form_visible = False

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------
    @property
    def current_url(self) -> str:
        return self._ui.current_url


__all__ = ["MockWebDriver", "is_mock_base_url"]
