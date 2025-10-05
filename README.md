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

### Running without a real XNAT deployment

When Docker or a browser stack is unavailable you can still exercise the
page-objects and scenarios using the bundled in-process mock XNAT server. This
mode keeps the tests runnable in CI sandboxes while continuing to validate the
automation logic.

```bash
export XNAT_USE_MOCK=1
pytest
```

The mock environment provides the default `admin` / `admin` credentials and
behaves like a simplified version of the real UI for the flows covered by the
suite.

## Running inside Docker

A Docker image is provided to run the Selenium suite with Google Chrome in
headless mode without installing dependencies locally.

1. Build the image:

   ```bash
   docker build -t xnat-selenium-tests .
   ```

2. Execute the tests, providing the XNAT connection details via environment
   variables. Additional Pytest arguments can be appended to the command.

   ```bash
   docker run --rm \
     -e XNAT_BASE_URL=https://your-xnat.example \
     -e XNAT_USERNAME=your-user \
     -e XNAT_PASSWORD=your-password \
     xnat-selenium-tests -m smoke
   ```

   By default the container launches `pytest`. Override the entrypoint to obtain
   an interactive shell if you need to inspect the environment:

   ```bash
   docker run --rm -it --entrypoint /bin/bash xnat-selenium-tests
   ```

## Local XNAT test environment

Spin up a disposable XNAT instance using the
[xnat-docker-compose](https://github.com/NrgXnat/xnat-docker-compose) project.
The helper script in `scripts/manage_xnat_test_env.sh` will clone or update that
repository inside `.xnat-test-env/` and proxy common Docker Compose commands.

1. Ensure Docker and Docker Compose are installed locally.
2. Start the stack:

   ```bash
   ./scripts/manage_xnat_test_env.sh up
   ```

   The services will be accessible on `http://localhost` with the default
   credentials `admin` / `admin` once the containers finish booting.
3. Point the Selenium tests at the local instance:

   ```bash
   export XNAT_BASE_URL=http://localhost
   export XNAT_USERNAME=admin
   export XNAT_PASSWORD=admin
   pytest -m smoke
   ```

4. When finished, stop or tear down the environment:

   ```bash
   ./scripts/manage_xnat_test_env.sh down    # stop containers
   ./scripts/manage_xnat_test_env.sh reset   # stop and remove volumes
   ```

Refer to the upstream repository for environment customization options such as
data persistence tweaks. For a fully automated local run (start stack, wait for
readiness, execute pytest, and tear the stack down) invoke the helper script:

```
./scripts/run_xnat_suite.sh
```

The script accepts optional overrides via environment variables, such as
`XNAT_BASE_URL`, `XNAT_USERNAME`, `XNAT_PASSWORD`, `TEARDOWN_ON_EXIT=false`, or
`WAIT_TIMEOUT=600`. When Docker is not available the helper automatically falls
back to the mock environment described above so the Selenium suite still runs.

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
