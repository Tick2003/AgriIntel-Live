# Contributing to AgriIntel.in

First off, thanks for taking the time to contribute! 🎉

---

## How Can I Contribute?

### Reporting Bugs

*   **Use a clear and descriptive title** for the issue.
*   **Describe the exact steps to reproduce** and what you expected vs. what happened.
*   **Include environment info**: OS, Python version, `pip list` output if relevant.
*   **Tag data pipeline bugs** with the `etl` label and include the relevant log lines from the GitHub Actions run.

### Suggesting Enhancements

*   **Use a clear and descriptive title**.
*   **Explain why this enhancement is useful** — ideally with a concrete farmer/stakeholder use-case.
*   **Describe alternatives you considered**.

### Pull Requests

1.  Fork the repo and create your branch from `main`.
2.  If you've added code that should be tested, **add tests** in `tests/`.
3.  If you've changed the data pipeline, run it locally with `--skip-swarm` first.
4.  Ensure the test suite passes: `pytest -m "not integration" -q`.
5.  Ensure zero lint errors: `ruff check .`
6.  Issue the pull request and fill in the PR template.

---

## Code Standards

### Logging
*   Use `logging.getLogger(__name__)` — never `print()`.
*   Use `%s` style format strings in log calls (`logger.info("msg %s", val)`), not f-strings.

### Imports
*   Group: stdlib → third-party → local (enforced by ruff `I001`).
*   One import per line (enforced by ruff `E401`).
*   Never use bare `except:` — always `except SomeError as exc:`.

### Security
*   All passwords must be hashed with `bcrypt` — never store plaintext.
*   `DEFAULT_ADMIN_PASSWORD` must be set in `.env` before running the app.
*   API endpoints require `X-API-Key` authentication.

### Data Pipeline
*   All new ETL sources must go through `DataReliabilityAgent.validate_batch()` before the database.
*   Add any new mandi GPS coordinates to `agents/reference_data.MANDI_COORDS` (single source of truth).
*   All new commodity/market names must be added to `TRACKED_COMMODITIES` / `TRACKED_MARKETS` in `agents/reference_data.py`.

---

## Git Commit Messages

*   Use the imperative mood: `Add feature`, not `Added feature`.
*   Limit the first line to 72 characters.
*   Use conventional commit prefixes: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `ci:`.
*   Reference issues after the first line: `Fixes #42`.

---

## Issue Labels

| Label | Meaning |
|-------|---------|
| `bug` | Broken functionality |
| `enhancement` | New feature or improvement |
| `documentation` | Docs update needed |
| `etl` | Data pipeline / ingestion issue |
| `ci` | GitHub Actions / workflow issue |
| `security` | Security-related concern |
