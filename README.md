# XNAT Selenium Test Suite (work in progress)

End-to-end Selenium tests that exercise key workflows in an XNAT deployment. The
suite focuses on authentication, project management, subject onboarding, and
basic imaging session registration so that new releases of an XNAT instance can
be validated automatically.

## Features

- Page Object Model abstractions for core XNAT screens (login, dashboard,
  projects, subjects, experiments).
- Pytest-powered fixtures that create browsers locally or via a remote Selenium
  grid, with configuration coming from environment variables or command line
  options.
- Smoke-level authentication coverage and a full project lifecycle scenario that
  provisions a project, subject, and imaging session.
- Marker definitions (`smoke`, `projects`, `e2e`) to aid targeted execution in
  CI pipelines.

## Getting started

1. Install dependencies (Python 3.10+):

   ```bash
   pip install -e .
   ```

2. Provide credentials and connection details for the target XNAT environment
   using environment variables or Pytest command line flags:

   - `XNAT_BASE_URL` / `--base-url`
   - `XNAT_USERNAME` / `--username`
   - `XNAT_PASSWORD` / `--password`
   - Optional: `XNAT_HEADLESS=0` (or use `--headed`) to run browsers with a UI.
   - Optional: `SELENIUM_REMOTE_URL` / `--remote-url` when using a Selenium
     server such as Selenium Grid or BrowserStack.

3. Run the tests:

   ```bash
   pytest
   ```

   Run only the fast smoke tests:

   ```bash
   pytest -m smoke
   ```

   Execute the end-to-end project lifecycle scenario:

   ```bash
   pytest -m e2e
   ```

## Project structure

```
src/xnat_selenium/      # Page objects and configuration helpers
└── pages/              # Specific page abstractions (login, dashboard, etc.)
tests/                  # Pytest suites leveraging the page objects
pyproject.toml          # Python package metadata and dependencies
pytest.ini              # Marker registration and Pytest defaults
```

## Notes

- The suite assumes the target XNAT instance uses the default user interface
  structure and element identifiers. Custom themes may require selector
  adjustments inside the page objects.
- Project, subject, and experiment names are generated dynamically to avoid
  collisions between repeated runs. Clean-up logic can be added if required by
  your governance policies.
