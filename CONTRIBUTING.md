# Contributing to PandexAI

Thanks for helping. This document covers how the project is put together, how to run
it locally, what CI checks, and how a change goes from your branch to npm.

## The one rule that shapes everything

PandexAI splits data work into two halves:

| Half | Who does it | Where it lives |
|---|---|---|
| **Execution** - any number computed from data (counts, nulls, medians, joins) | Python / pandas, deterministically | `scripts/` |
| **Judgment** - interpreting results, deciding what matters, writing summaries | The AI CLI (Claude Code, Cursor, ...) | `SKILL.md`, `commands/*.md`, `.claude/commands/pandex.md` |

Every script prints a **single JSON object** to stdout and exits `0` on success or `1` with
`{"error": "..."}` on failure. The markdown files tell the AI which fields to read and
explicitly forbid it from recomputing or guessing them. If you change what a script
prints, you must update the matching markdown file in the same PR. That contract is
the product.

## Repository layout

```
bin/pandex.js              npx installer: creates .pandex/venv, installs pandas+openpyxl,
                           copies SKILL.md, commands/, scripts/, .claude/ into the user's project
scripts/
  loaders.py               load_dataframe(path) -> (df, duplicate_column_names, encoding_note)
  cleaner.py               pure-pandas transforms + clean_dataframe() orchestrator
  clean.py                 CLI entry: clean_file(path) -> writes <name>_cleaned_results/*.xlsx, prints JSON
  gatherer.py              join-column detection (name AND value overlap) + outer-join / linked-sheets
  gather.py                CLI entry: gather_files(paths) -> writes <first>_gathered_results/gathered.xlsx
  checks.py                data-quality heuristics used by profile.py
  profile.py               CLI entry: per-column profile (not yet exposed as a /pandex subcommand)
commands/*.md              per-command instructions for the AI (input, how to run, JSON fields, tone)
.claude/commands/pandex.md the /pandex slash command router (clean | gather | analyze-stub)
SKILL.md                   the top-level skill file the AI reads first
tests/                     pytest suite: unit tests, real-data end-to-end tests, CLI contract tests
real_data/                 unmodified public datasets (Titanic, UCI, OpenFlights, Northwind); see its README
test_fixtures/             failure-path inputs only: empty file, corrupted .xlsx, latin-1 file, one hand-made edge case
```

The scripts use flat imports (`from loaders import ...`) on purpose: they are copied
into end-user projects as loose files with no package install, so they must run as
`python scripts/clean.py` from any working directory.

## Local setup

Requirements: Python 3.10+ and Node 18+.

```bash
git clone https://github.com/jahirulanik/pandexai
cd pandexai
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

Run the scripts directly against the fixtures:

```bash
python scripts/clean.py real_data/uci_adult_sample.csv
python scripts/gather.py real_data/northwind_customers.csv real_data/northwind_orders.csv
python scripts/profile.py real_data/titanic.csv
```

Output folders (`*_cleaned_results/`, `*_gathered_results/`) are written next to the
input file. Don't commit new ones.

## Running the checks

| What | Command | Notes |
|---|---|---|
| Lint | `ruff check scripts tests` | `ruff check --fix` auto-fixes import order |
| Tests | `pytest` (or `npm test`) | ~10 s. Real-data tests and CLI tests run the scripts as subprocesses, exactly like the AI does |

CI runs both on every push and PR (see below). Please run them before opening a PR.

## Writing tests

The rule: test against real data, not data invented to pass. There is no smoke test.

- **Real datasets** are the primary tests. `tests/test_real_data.py` runs `clean` and
  `gather` on the files in `real_data/` and asserts on the report. Expected numbers must
  be recomputed from the raw file inside the test with plain pandas, or be documented
  properties of the dataset (Titanic has 891 rows and 177 missing ages). When you fix a
  bug found on real data, add the dataset (or a contiguous slice of it) and a test that
  fails without the fix. `real_data/README.md` explains how to add one.
- **Pure transforms** (`cleaner.py`, `gatherer.py`, `checks.py`) get unit tests in
  `tests/test_cleaner.py` / `tests/test_gatherer.py`. Build a tiny `pd.Series` inline;
  assert both the transformed values and the change count.
- **The JSON contract** (field names, exit codes, output file names, friendly error
  text) is in `tests/test_scripts_cli.py`. `test_fixtures/` holds only inputs that cannot
  be downloaded: an empty file, a corrupted `.xlsx`, a latin-1 export, and one hand-made
  CSV that has a same-ID conflict and a fully empty row in the same file.
- Watch for **null handling**. pandas 3 uses a `str` dtype where `NaN != NaN` and
  `NA` comparisons are truthy. Counts must be computed with `_count_changes()` in
  `cleaner.py`, never with `(a != b).sum()` over a column that may contain nulls.
  We've been bitten by this three times.
- New file-format or edge-case inputs go in `test_fixtures/` and stay small (< 50 KB,
  `large_data.csv` is the one exception).

## Making a change

1. Branch from `main`: `git checkout -b feat/short-description` or `fix/...`.
2. Keep PRs focused on one command or one rule. A new cleaning rule is one PR; the
   docs update for it is part of the same PR, not a second one.
3. Add or update tests. If the JSON report gained or renamed a field, update
   `commands/<command>.md` so the AI knows about it.
4. **Do not bump the version.** Maintainers bump `package.json` + `pyproject.toml`
   together at release time.
5. Open the PR; the template will ask you to tick the checklist.

### Adding a new `/pandex` subcommand

1. `scripts/<name>.py` - CLI entry that prints one JSON object, plus a pure module
   (`scripts/<name>er.py`) with the pandas logic, following `clean.py` / `cleaner.py`.
2. `commands/<name>.md` - what it does, how to run it, which JSON fields to present,
   what to say to the user. Copy the structure of `commands/clean.md`.
3. Add a branch to `.claude/commands/pandex.md` and a line to `SKILL.md`.
4. Unit tests in `tests/test_<name>er.py`, and a real-data test in `tests/test_real_data.py`.
5. Nothing in `bin/pandex.js` needs to change: it copies whole directories.

### Adding a cleaning rule

Add a function `rule(series) -> (new_series, changed_count)` in `cleaner.py`, wire it
into the per-column loop in `clean_dataframe()`, add its count key to the
`columns_cleaned` report, and document that key in `commands/clean.md`. Rules must be
conservative: when unsure, leave the data alone and let the AI flag it. Find a public
dataset that needs the rule and add it to `real_data/` with a test; a rule nothing real
needs is a rule we do not add.

Two mistakes we have already made, so you do not have to:

- Substring checks on column names. `"id" in name` matched `width` and `paid`. Use
  `is_id_column()`.
- Counting changes with `(before != after).sum()`. NaN never equals NaN, so every null
  cell counted as a change. Use `_count_changes()`.

## Style

- Python: `ruff` with `E`, `F`, `I` rules, 120-column lines. No type-checker yet.
- Prefer plain functions over classes. No new runtime dependencies beyond pandas and
  openpyxl without a discussion first: everything gets `pip install`ed into every
  user's project.
- Error messages shown to end users are plain English, no stack traces. Add new cases
  to `friendly_error_message()` in the relevant entry script.
- Commit messages: imperative, explain the *why* in the body if it isn't obvious.

## CI/CD

`.github/workflows/ci.yml` runs on every push to `main`, every PR, and on demand:

| Job | What it checks |
|---|---|
| `lint` | `ruff check`; `ruff format --check` is advisory only for now |
| `python-tests` | `pytest` on Python 3.10 and 3.13 across Ubuntu, Windows, macOS, plus 3.11/3.12 on Ubuntu. Python 3.10 gets pandas 2.x, 3.11+ gets pandas 3.x, so both are covered |
| `package-consistency` | `package.json` and `pyproject.toml` versions match; every `files` entry exists; tarball has no `__pycache__`, tests, real data, or sandbox |

`.github/workflows/release.yml` runs when a `v*.*.*` tag is pushed: it verifies the tag
equals the `package.json` version, re-runs the full CI workflow, publishes to npm with
provenance, and creates a GitHub Release with auto-generated notes.

### Releasing (maintainers)

One-time setup: create an npm **Automation** token and add it as the `NPM_TOKEN`
secret in a GitHub environment named `npm` (Settings -> Environments). Optionally add
required reviewers to that environment to gate publishes.

Per release:

```bash
git checkout main && git pull
# bump BOTH files to the same version
npm version 0.1.15 --no-git-tag-version
sed -i '' 's/^version = ".*"/version = "0.1.15"/' pyproject.toml   # macOS sed; drop '' on Linux
# add a section to CHANGELOG.md
git commit -am "Release 0.1.15"
git tag v0.1.15
git push origin main --tags
```

The `Release` workflow does the rest. If it fails at the verify step, the tag and
`package.json` disagree: delete the tag, fix, re-tag.

## Reporting bugs and proposing features

Use the issue templates. For bugs, a 3-5 row sample file that reproduces the problem
is worth more than any amount of description.

## License

By contributing you agree your contributions are licensed under the MIT License in
`LICENSE`.
