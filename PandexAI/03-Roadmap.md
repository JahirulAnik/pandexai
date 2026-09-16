# PandexAI — Roadmap

## Phase 0 — Foundation (COMPLETE, 2026-08-29)

All of the following were proven end-to-end, not just written:

1. Naming and registration across GitHub, npm, and PyPI
2. Repo skeleton (`commands/`, `scripts/`, `connectors/` placeholder)
3. `SKILL.md` — the judgment/execution split as a hard rule
4. `commands/scan.md`
5. `scripts/profile.py` (original single-file version)
6. `npx pandexai init` packaging (auto-venv strategy) — verified via a real `npx` invocation from the live npm registry in a clean folder
7. A full manual AI CLI test in Claude Code: given only a plain-language instruction (no slash command yet), Claude Code correctly read the instruction files, ran the real script, and added genuine judgment on top of the computed numbers — exactly the intended architecture.

## `scan` renamed to `clean` (2026-08-31)

Following a real-world mapping exercise (what does a data analyst's "clean data" step actually involve — filling missing values, removing duplicates, correcting errors, standardizing formats), the user decided `scan` should stop being read-only diagnosis and start actually fixing issues. Rather than adding a separate `clean` command, `scan` was renamed to `clean` and given real fixing behavior (dedupe, casing standardization, blank normalization, missing-value fill) on top of its existing diagnosis. See `02-Commands.md` and `04-Decision-Log.md` for full details. `scan`'s diagnosis-only logic (`profile.py`) is kept in the codebase but no longer wired up as a live command.

## Phase 1 — Hardening `clean` (formerly `scan`) (IN PROGRESS)

Chosen focus: harden the one existing command before adding new ones, since every future command (`gather`, `analyze`, etc.) will build on the same file-reading and data-quality-check foundations.

| # | Item | Status |
|---|---|---|
| 1 | Make `/pandex scan` (now `clean`) a real typed slash command | ✅ Done |
| 2 | Duplicate detection + core data-quality checks (blanks, casing) | ✅ Done |
| 3 | File type support: Excel (.xlsx/.xls), JSON | ✅ Done |
| 4 | Edge cases: empty file, one-column file, all-null columns, non-UTF8 encoding | ✅ Done |
| 5 | Large file handling: size/row check, sampling or chunked reading | ⬜ Tested, deprioritized (see note below) |
| 6 | Better error messages: catch common failures with plain-English reasons instead of raw Python errors | ✅ Done |
| 7 | Test fixture set: a folder of sample files (clean, messy, empty, huge, non-UTF8) to verify everything above stays working as more features are added | ✅ Done - `test_fixtures/` folder committed to the repo |
| 8 | Actual data cleaning (rename `scan` → `clean`): remove duplicates, standardize casing, normalize blanks, fill missing values, standardize dates and known categories | ✅ Done, verified via script AND the real `/pandex clean` slash command, published as **pandexai@0.1.6** |

**All 8 items on the `scan`/`clean` hardening roadmap are now complete.**

### Large file test (2026-08-31)

Before building anything for item 5, tested current behavior against a real 1,000,000-row (~47 MB) CSV with realistic messy data (duplicate IDs, inconsistent casing, blank regions). Result: `scripts/profile.py` completed in ~6.3 seconds with no memory issues or crashes, using the existing code as-is (no sampling or chunking). Confirmed via a real `/pandex scan bigfile.csv` run in Claude Code, not just the raw script.

The AI's summary was a strong validation of the judgment/execution split at scale:
- Correctly explained duplicate `order_id` values by noticing the ID range (max 799,999) was smaller than the row count (1M) — reasoning not explicitly present in the JSON output.
- Correctly distinguished "duplicate values in an ID column" from "duplicate rows" (the JSON reported 0 duplicate rows).
- Flagged that `order_date` was stored as a string rather than a datetime — an issue the script does **not** check for at all. Pure AI-added judgment on top of real computed facts.
- Proactively suggested a sensible next step ("fix the region casing and nulls").

**Conclusion:** current performance is good enough that large-file handling (sampling/chunking) is not urgent. Deprioritized in favor of `gather`. Revisit if real users hit files large enough to cause actual memory/time problems (likely multi-GB / tens of millions of rows).

## Phase 2 (future) — Beyond `scan`

Not started, order not yet finalized:

- `/pandex gather` — combine multiple files into one working dataset (design already discussed, see `02-Commands.md`)
- `/pandex analyze` — correlations, trends, group comparisons
- `/pandex validate` — check data against business rules
- `/pandex compare` — compare two datasets or time periods
- `/pandex anomalies` — flag outliers and unexpected patterns

## Explicitly deferred (not on the near-term roadmap)

- **Public website** — branding/marketing/docs site, modeled on tools like Cursor/Claude Code/OpenCode. Decision made to build this, but explicitly deferred until core Phase 1 work is done. No website research or building until the user gives an explicit go-ahead.
- **Domain registration** (`pandex.ai` or similar) — optional, tied to the website work above.
- **Export integrations** (Notion, Power BI) — realistic path to "sharing results with a team" without PandexAI building its own hosted multi-user product. Deferred until `gather`/`analyze` exist, since there needs to be a finished analysis to export.
- **Multi-user / hosted dashboard** — explicitly out of scope for PandexAI as a local CLI tool. See the honest scope assessment in `04-Decision-Log.md`.

## Honest scope assessment

A rough estimate discussed with the user: PandexAI, in its current and near-term planned form, can realistically cover about **15-20%** of a typical data analyst's full job — the file-based data cleaning, validation, and light analysis slice. It is not, and isn't intended to become, a replacement for BI dashboard tools (Power BI, Cognos) or data-engineering/ETL orchestration platforms (PySpark, Snowflake pipelines). This is treated as the honest, correct positioning rather than a limitation to hide.
