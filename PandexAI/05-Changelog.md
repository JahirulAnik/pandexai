# PandexAI — Changelog

## pandexai@0.0.1 (npm) / 0.0.1 (PyPI)
- Initial placeholder publish. npm tarball contained only LICENSE, README.md, package.json — no functional code yet.

## pandexai@0.1.0
- First functional release. Added `bin/pandex.js` (the `npx pandexai init` entry point), `SKILL.md`, `commands/scan.md`, `scripts/profile.py`.
- `package.json` updated with a proper `bin` field and `files` list so the real functional files are actually included in the published package.
- `npx pandexai init` verified working end-to-end from the live npm registry.

## pandexai@0.1.1
- No functional change to `scan` itself — republished after fixing a `package.json` version bump issue during testing.

## pandexai@0.1.2
- **Fixed:** `/pandex scan` now works as a real typed slash command in Claude Code.
- Added `.claude/commands/pandex.md` (the actual Claude Code custom-command file).
- Updated `bin/pandex.js` to copy `.claude` into new projects during `init`.
- **Root cause of the original bug:** `.claude` also needed to be added to `package.json`'s `"files"` array — copying it in `bin/pandex.js` alone was not sufficient, since files not listed in `"files"` never reach the published npm tarball.

## pandexai@0.1.3
- Added duplicate-row detection (count + example rows).
- Added duplicate-value detection for identifier-like columns (name-based heuristic: any column with "id" in its name).
- Added detection of duplicate column names in the source file.
- Added "blank-like" value detection (empty strings, "N/A", "-", "null", "none", "unknown" as literal text).
- Added inconsistent-casing detection (e.g. "North" vs "north").
- Updated `commands/scan.md` to instruct the AI to specifically call out these new fields as data quality issues.

## pandexai@0.1.4
- Added Excel (.xlsx, .xls) and JSON file support to `scan`, alongside CSV.
- Refactored `scripts/profile.py` into three modules: `loaders.py` (file reading), `checks.py` (data-quality checks), `profile.py` (thin orchestrator) — for easier future maintenance.
- Added `openpyxl` as a dependency, now installed automatically by `bin/pandex.js` during `init`.
- Updated `commands/scan.md` to mention all three supported file formats.
- Verified end-to-end with real Excel and JSON test files, including a live `/pandex scan test.xlsx` run in Claude Code producing a strong, correct AI summary.

## pandexai@0.1.5
- Added edge-case hardening to `scan`:
  - Empty (0-byte) CSV files now raise a clear, graceful error instead of crashing.
  - Files with zero data rows return a `"warning"` field instead of misleading stats.
  - Columns where every value is null are now flagged with `"all_values_null": true` plus an explanatory note.
  - Non-UTF8 CSV files (e.g. exported from Excel on Windows) now fall back automatically to latin-1 encoding instead of crashing, with an `"encoding_note"` returned so the AI can flag it to the user.
  - Excel/JSON files with no columns or rows are also caught and reported cleanly.
- Updated `commands/scan.md` with new instructions telling the AI how to present warnings, all-null columns, and encoding notes to the user.
- Verified end-to-end: empty file, all-null column, one-column file, and a real non-UTF8 (Windows-1252) file all tested and confirmed working correctly.

## Large-file validation (2026-08-31, no version change)
- Generated a realistic 1,000,000-row (~47 MB) test CSV and ran a real `/pandex scan` on it in Claude Code.
- No code changes needed: current `scripts/profile.py` completed in ~6.3 seconds with correct results (duplicate detection, casing, nulls all worked correctly at scale).
- AI summary correctly added judgment beyond the raw JSON, including flagging `order_date` being stored as a string instead of a datetime — a check the script itself does not perform.
- Decision: deprioritize large-file handling (item 5 on the scan roadmap) until real usage shows an actual need (much bigger files).

## pandexai@0.1.6 (2026-09-01) - scan renamed to clean, published
- **`/pandex scan` renamed to `/pandex clean`.** The command now diagnoses AND actively fixes data quality issues instead of just reporting them.
- Added `scripts/cleaner.py`: the cleaning logic — remove exact duplicate rows, standardize inconsistent casing, normalize blank-like text to real nulls, trim whitespace, and fill missing values (median for numeric columns, "Unknown" for text columns).
- Added `scripts/clean.py`: entry point that loads a file, applies cleaning, and writes a new `<name>_cleaned.<ext>` file — the original file is never modified. Prints a JSON report of exactly what changed.
- Renamed `commands/scan.md` to `commands/clean.md` and updated `.claude/commands/pandex.md` to route the `clean` subcommand instead of `scan`.
- `scripts/profile.py` (the old diagnosis-only script) is kept in the codebase for now but is no longer wired to a live command.
- Fixed two real bugs found during manual testing on a messy test CSV:
  - A pandas 3.x dtype change (`object` → `"str"` for text columns) meant the cleaning logic's `dtype == object` checks silently never ran on any real text column. Fixed by switching to `not pd.api.types.is_numeric_dtype(series)`.
  - Duplicate-row removal originally ran before casing/blank normalization, so near-duplicate rows differing only by formatting weren't caught. Fixed by moving dedup to the end of the pipeline.
- Verified via direct script test (`python scripts\clean.py cleantest.csv`) with correct results after both fixes. **Verified via the real `/pandex clean` slash command in Claude Code** (run from a session opened directly in the repo folder) - correctly recognized as a subcommand, presented a clear column-by-column change table, confirmed the original file was untouched, and added genuine AI judgment (flagged that half of a date column's values were synthetically filled and shouldn't be trusted for time-based analysis). **Published as pandexai@0.1.6.**

## pandexai@0.1.6 continued - additional clean features and hardening (same release)
- Added date field normalization: columns whose values mostly look like dates (mixed formats like `2024-01-05`, `01/06/2024`, `Jan 7 2024`) get standardized to a consistent `YYYY-MM-DD` format. Uses `format="mixed"` in pandas so different formats within the same column parse correctly instead of pandas forcing one inferred format on the whole column.
- Added known-category standardization: columns made up entirely of recognized abbreviations/variants for one concept (`m`/`male`/`f`/`female`, `y`/`yes`/`n`/`no`, `t`/`true`/`f`/`false`) get mapped to a canonical spelled-out form. Only triggers when every value in the column matches one known group, to avoid misfiring on unrelated data.
- Measurement unit standardization (e.g. kg vs lbs) was explicitly deferred - too risky to auto-convert without real example data to design against safely; can revisit later.
- Added plain-English error messages for common failure cases (file not found, corrupted/invalid Excel file, permission denied, malformed CSV) instead of raw Python exception text, via a new `friendly_error_message()` function in `clean.py`.
- Built a permanent `test_fixtures/` folder in the repo: clean_data.csv, messy_data.csv, empty_file.csv, all_null_column.csv, mixed_encoding.csv, one_column.csv, large_data.csv (10k rows), and corrupted.xlsx - covers every known edge case so future changes can be quickly re-verified without manually recreating test files each time.
- All scan-hardening roadmap items (1-7) are now complete.

## pandexai@0.1.7-0.1.13 (2026-09-02, published incrementally) - clean output overhaul
Major rework of what `clean` actually produces, driven by real analyst-workflow feedback (comparing against a "Clean Data" slide covering missing values, duplicates, formatting standardization, and validation).

- **Excel AutoFilter** added to `.xlsx` outputs via a new `add_excel_autofilter()` function in `clean.py` (uses `openpyxl`'s `worksheet.auto_filter.ref` after `pandas.to_excel()`, since pandas itself has no filter support). Later extended to also auto-size every column's width based on content length.
- **Results-folder restructure:** `clean` no longer writes a single `<name>_cleaned.<ext>` file next to the original. It now creates a `<name>_cleaned_results/` folder containing up to 5 files, so no data is ever silently lost or hidden:
  - `cleaned.xlsx` - the final cleaned data (always created)
  - `duplicates.xlsx` - exact duplicate rows (all copies, not just extras), only if any exist
  - `conflicts.xlsx` - **new category**: rows sharing the same ID but differing in other fields (e.g. same `customer_id` with different `gender`/`amount`) - these are NOT caught by exact-duplicate detection and previously slipped through untouched into the cleaned file silently. Now flagged separately for human review.
  - `missing_values.xlsx` - original (pre-fill) rows that had some but not all fields missing
  - `empty_rows.xlsx` - rows that were completely blank
  - Every review file (duplicates/conflicts/missing_values/empty_rows) is ALWAYS saved as `.xlsx` with AutoFilter and auto-sized columns, regardless of the input file's format - since these are meant for a human to review in Excel. Only `cleaned.xlsx` used to match the input format, but this was later changed too (see below).
  - **`cleaned.xlsx` also now always saves as `.xlsx` with AutoFilter** (was previously matching the input file's extension, e.g. staying `.csv`), so the user can filter/sort by any column (region, date, gender, status, etc.) directly in Excel - this was an explicit late request ("filtering system... separate data by date or regionally").
- **Single `reason` column instead of differently-named tag columns.** Originally each output file used a different column name (`missing_columns`, `duplicate_group`, `conflicting_columns`) - simplified to one consistent `reason` column per file with a plain-English sentence (e.g. `"Missing values in: amount | signup_date"`, `"Same customer_id as another row, but differs in: gender | amount"`). Also switched the internal separator from `, ` to ` | ` after discovering that a comma embedded in an unquoted-looking CSV cell confuses Excel's "Text to Columns" and double-click-to-open behavior, scrambling the row across extra columns.
- **Fixed a real empty-row-detection bug:** a row with only an ID and every other field blank (e.g. `customer_id: 4`, nothing else) was not being classified as "fully empty," because the check originally looked at every column including the ID. Fixed by excluding ID-like columns (name contains "id") from the emptiness check - `check_cols = [c for c in working.columns if c != id_col]`.
- **`clean_dataframe()` signature changed** to return 6 values: `(cleaned_df, report, duplicates_df, missing_df, empty_rows_df, conflicts_df)`.

### Debugging note: npm/npx caching traps (worth remembering)
Several rounds of "the fix isn't showing up in the sandbox" turned out to NOT be code bugs at all, but publish/cache issues:
1. Code was written and even `git commit`-ed locally, but `npm publish` was never actually run before testing in the sandbox - `git status` showing "nothing to commit" was the tell that a supposed fix was never saved to disk in the first place; `git diff` on individual files helped isolate what was genuinely pending.
2. Even after a real `npm publish`, `npx pandexai init` in the sandbox kept installing an OLD cached version. Root cause: `npx <package>` (without `@latest`) can resolve from npx's local cache instead of hitting the registry. Fix: `npm cache clean --force` followed by `npx --yes pandexai@latest init` (explicit `@latest`, not just the bare package name) reliably forces a fresh pull.
- Lesson for future debugging: when "the sandbox isn't picking up a change we're sure we made," check in this order: (1) does the source file on disk actually have the change (`type <file> | findstr <marker>`), (2) is it committed (`git status`/`git diff`), (3) was it actually published (`npm publish` output, `npm view pandexai version` vs `package.json` version), (4) is the sandbox actually fetching fresh (`npm cache clean --force` + `npx --yes <pkg>@latest`).

**Status: `clean` is now considered feature-complete for this round.** Verified end-to-end with a synthetic 100-row test file (`large_test.csv`) covering casing, gender variants, mixed date formats, blank placeholders, missing fields, fully empty rows, exact duplicates, and same-ID conflicts - all 5 output files produced correctly with working AutoFilter.
