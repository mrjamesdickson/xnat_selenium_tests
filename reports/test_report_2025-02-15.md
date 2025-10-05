# Pytest Execution Report

- **Command:** `source .venv/bin/activate && python3 -m pytest tests --base-url="https://crdemo.dev.xnatworks.io" --username="admin" --password="admin"`
- **Date:** 2025-10-05 21:16:35Z

## Summary
- **Total tests:** 35
- **Passed:** 21
- **Skipped:** 14
- **Failed:** 0
- **Warnings:** 1 (`RuntimeWarning` about the base URL returning HTTP 503 on HEAD request)

## Skipped Test Reasons
All skipped tests failed to start the Selenium Chrome driver in the containerized environment:
- `tests/test_dashboard_navigation.py` (2 tests)
- `tests/test_login.py` (3 tests)
- `tests/test_project_lifecycle.py` (2 tests)
- `tests/test_project_management.py` (3 tests)
- `tests/test_subject_and_experiment_management.py` (4 tests)

Each skip reported: *"Unable to obtain driver for chrome"* with a link to Selenium driver troubleshooting guidance.

## Additional Notes
- The HEAD request to `https://crdemo.dev.xnatworks.io` returned HTTP 503, but the test suite continued after logging a warning.
- Review the test infrastructure to ensure the required Chrome driver and browser binaries are available when running Selenium UI tests.
