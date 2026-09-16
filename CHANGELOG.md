# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed
- `clean`: `whitespace_trimmed`, `categories_standardized` and `dates_standardized`
  counts in the JSON report no longer include null cells (NaN != NaN was being counted
  as a change; more visible under pandas 3's `str` dtype).
- `npx pandex init` success message referenced the removed `scan` command.
- npm tarball no longer includes `__pycache__` bytecode.

### Added
- pytest suite (`tests/`) covering the pandas transforms, join detection, and the
  scripts' JSON/exit-code contract against `test_fixtures/`.
- Node smoke test that packs the package and runs `pandex init` in a fresh project.
- GitHub Actions CI (lint, Python 3.10-3.13 on Linux/Windows/macOS, installer smoke on
  Node 18/22, package consistency) and a tag-driven npm release workflow.
- `CONTRIBUTING.md`, PR template, issue templates.
- `pyproject.toml` now declares dependencies, ruff and pytest config; version aligned
  with `package.json`.

## [0.1.14] - 2026-09-16

- Add `/pandex gather`: joins files on a real shared column (name + value overlap),
  falls back to linked sheets if no reliable connection exists.
- `cleaned.xlsx` always saved as .xlsx with AutoFilter.
- Review files (duplicates, conflicts, missing_values, empty_rows) saved as formatted .xlsx.
- Conflict detection for same-ID rows with differing data.
