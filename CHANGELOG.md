# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed
- `clean`: columns whose name merely contained "id" (`width`, `valid`, `paid`, `holiday`)
  were treated as the ID column. On the UCI Automobile data this produced 190 false
  "conflicting duplicate" rows. Only whole-word ids count now (`id`, `order_id`,
  `Order ID`, `customerID`, `PassengerId`).
- `clean`: `?`, `\N`, `NULL`, `#N/A`, `--`, `nil`, `missing` are now recognised as
  missing values. Previously 244 `?` cells in a UCI Adult sample and 1496 `\N` cells in
  OpenFlights data survived untouched.
- `clean`: numeric columns that pandas read as text because of a missing marker
  (`price` with a `?`) were filled with the string "Unknown". They are converted back to
  numbers and filled with the median; the report shows `converted_to_numeric`.
- `gather`: results were written into the current working directory instead of next to
  the first input file.
- `clean`: `whitespace_trimmed`, `categories_standardized` and `dates_standardized`
  counts in the JSON report no longer include null cells (NaN != NaN was being counted
  as a change; more visible under pandas 3's `str` dtype).
- `npx pandex init` success message referenced the removed `scan` command.
- npm tarball no longer includes `__pycache__` bytecode.
- `clean`'s no-filename fallback could return a path with mixed `\` and `/` separators
  on Windows, since joining a path doesn't normalize slashes already inside a string.
  Fixed with `os.path.normpath`.

### Added
- `/pandex profile <file>`: read-only per-column statistics and data-quality signals
  (nulls, blank-like values, inconsistent casing, duplicate values) for a single file.
  Nothing is written to disk.
- `/pandex analyze [file]`: the full read-only analysis - everything `profile` reports,
  plus correlations between numeric columns, trends over time (when a date column is
  found, bucketed into an auto-picked day/week/month/year period), group-by comparisons
  ("average order value by region"), and outlier flagging (IQR fences). Falls back to
  the last gathered file when run with no filename, same as `clean`.
- `gather` with no filenames auto-discovers every CSV/Excel/JSON file in the project
  folder and combines them, instead of requiring filenames every time.
- `gather` remembers its own output, so `clean` and `analyze` run with no filename
  automatically pick up and operate on whatever `gather` last produced.
- CSV files with a few malformed lines (unquoted commas, typical of SQL exports) are
  read anyway; the lines are skipped and reported as `malformed_rows_skipped` and
  `malformed_row_numbers`. `gather` reports the same per file under `file_notes`.
- `real_data/`: unmodified public datasets (Titanic, UCI Adult, UCI Automobile,
  OpenFlights airlines, Northwind customers and orders) with a README of sources.
- pytest suite (`tests/`): real-data end-to-end tests whose expected values are
  recomputed from the raw files, unit tests for every transform, and CLI contract tests.
- GitHub Actions CI (lint, Python 3.10-3.13 on Linux/Windows/macOS, package
  consistency) and a tag-driven npm release workflow.
- README diagrams of the architecture, the `clean` pipeline and the `gather` decision,
  plus a results table on the real datasets.
- `CONTRIBUTING.md`, PR template, issue templates.
- `pyproject.toml` now declares dependencies, ruff and pytest config; version aligned
  with `package.json`.

## [0.1.14] - 2026-09-16

- Add `/pandex gather`: joins files on a real shared column (name + value overlap),
  falls back to linked sheets if no reliable connection exists.
- `cleaned.xlsx` always saved as .xlsx with AutoFilter.
- Review files (duplicates, conflicts, missing_values, empty_rows) saved as formatted .xlsx.
- Conflict detection for same-ID rows with differing data.
