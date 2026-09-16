# PandexAI — Architecture

## Repository layout

```
pandexai/
├── bin/
│   └── pandex.js          # npx entry point — handles `init`
├── scripts/
│   ├── profile.py         # (legacy) diagnosis-only orchestrator, superseded by clean.py
│   ├── clean.py            # entry point for the clean command (diagnose + fix)
│   ├── cleaner.py          # cleaning logic: dedupe, casing, blanks, fill missing
│   ├── loaders.py         # reads CSV / Excel / JSON into a DataFrame
│   └── checks.py          # data-quality check functions (used by profile.py)
├── commands/
│   └── clean.md            # plain-language instructions an AI reads to run clean
├── .claude/
│   └── commands/
│       └── pandex.md      # the REAL registered slash command for Claude Code
├── SKILL.md                # master index: judgment/execution rule + command list
├── package.json
├── pyproject.toml
├── LICENSE
└── README.md
```

## How `npx pandexai init` works

Implemented in `bin/pandex.js`. On running `npx pandexai init` inside a project folder, it:

1. Detects a working `python3`/`python` on PATH (fails loudly with a clear message if none found).
2. Creates an isolated virtual environment at `.pandex/venv` inside the user's project (skips this step if one already exists).
3. Installs `pandas` and `openpyxl` into that venv.
4. Copies `SKILL.md`, `commands/`, `scripts/`, and `.claude/` from the package into the user's project.

This is the **auto-venv strategy** — chosen over pipx (breaks the single-command pitch) and global pip install (dependency conflict risk with the user's own Python environment).

## Two different "command" concepts — do not confuse these

This tripped us up once during development, worth documenting clearly:

- **`commands/clean.md`** — a plain markdown file with instructions written *for an AI to read*. On its own this does **not** register anything with an AI CLI. An AI can be told in plain language ("read commands/clean.md and run clean") to follow it, but typing `/pandex clean` will NOT work from this file alone.
- **`.claude/commands/pandex.md`** — this is the actual mechanism Claude Code uses to recognize a real typed slash command. A file here named `pandex.md` is what makes `/pandex <subcommand> [file]` work as a literal command in the terminal.

Both files currently exist and are kept in sync; `.claude/commands/pandex.md` is the one that makes the command actually run when typed.

## Critical packaging gotcha

A file being copied by `bin/pandex.js`'s internal copy logic is **not enough** to get it into a user's installed package. npm only publishes what is listed in `package.json`'s `"files"` array. Early on, `.claude` was being copied by the script but wasn't listed in `"files"` — so it silently never made it into the published tarball, and `/pandex scan` (as it was named at the time) failed with "Unknown command" for every real user even though local testing worked. Lesson: **any folder `bin/pandex.js` copies must also be listed in package.json's `"files"` array**, or it will never exist in a real install.

## `scripts/` module breakdown

Originally `profile.py` was a single growing file. It was split into three modules (2026-08-30) to keep future changes small and safe to review:

- **`loaders.py`** — `load_dataframe(path)` detects the file extension (`.csv`, `.xlsx`/`.xls`, `.json`) and returns `(dataframe, duplicate_column_names, encoding_note)`. Duplicate column names are detected by reading the raw header before pandas silently auto-renames collisions (e.g. `amount` + `amount` → `amount` + `amount.1`). Also handles edge cases (added 2026-08-30/31): raises a clear error on 0-byte CSV files or files with no columns/rows (Excel/JSON too), and falls back from UTF-8 to latin-1 on `UnicodeDecodeError` (returning an `encoding_note` string explaining the fallback) instead of crashing on non-UTF8 files such as CSVs exported from Excel on Windows.
- **`checks.py`** — all data-quality check functions, each independent and reusable:
  - `duplicate_row_summary(df)` — full-row duplicate count + example rows
  - `duplicate_value_summary(series, column_name)` — flags duplicate values in identifier-like columns (see heuristic below)
  - `count_blank_like(series)` — counts values like `""`, `"N/A"`, `"-"`, `"null"`, `"none"`, `"unknown"` (as literal text) that pandas' normal null detection misses
  - `check_inconsistent_casing(series)` — flags things like `"North"` vs `"north"` being treated as different categories
  - `safe_float(value)` — safely converts to a rounded float or `None`, handling NaN
- **`profile.py`** — (legacy, diagnosis-only) imports from both modules and assembles the final JSON result. Kept in the codebase but no longer wired up as the live command; superseded by `clean.py`.
- **`cleaner.py`** (added 2026-08-31) — the actual cleaning logic, independent of loading/saving:
  - `normalize_blank_like(series)` — converts blank-like text ("", "N/A", "-", "null", "none") to real NaN
  - `trim_whitespace(series)` — strips leading/trailing whitespace from text values
  - `standardize_casing(series)` — for each lowercase value, finds the most frequent casing variant and replaces all others with it
  - `fill_missing(series)` — fills nulls: **median** for numeric columns, **`"Unknown"`** for text columns (decided with the user, see `04-Decision-Log.md`)
  - `clean_dataframe(df)` — orchestrates all of the above per-column, then removes exact duplicate rows **last** (after normalization, not before — see the bug note below), and returns `(cleaned_df, report)`
- **`clean.py`** (added 2026-08-31) — the entry point (`python clean.py <path>`). Loads the file via `loaders.py`, runs `cleaner.clean_dataframe`, saves the result to a new `<name>_cleaned.<ext>` file (never overwrites the original), and prints a JSON report of what changed.

### Bug found and fixed while building `clean` (2026-08-31)

Two real bugs surfaced during manual testing on a deliberately messy CSV, both worth remembering:

1. **pandas 3.x dtype change.** The cleaning code originally checked `if series.dtype == object:` before running blank-normalization, whitespace-trimming, and casing-standardization. But pandas 3.0 (the version installed here) changed the default storage for text columns from `object` to a new `"str"` dtype — so that check was silently always `False`, and the entire block never ran on any real text column. Only `fill_missing` worked, since it didn't have that same check. **Fix:** changed the condition to `if not pd.api.types.is_numeric_dtype(series):` — robust to both the old and new pandas string storage.
2. **Dedup-before-normalize ordering bug.** Duplicate row removal originally ran *before* casing/blank normalization, so two rows that were logically identical (e.g. differing only by `"south"` vs `"South"`, or `""` vs `"-"`) weren't caught as duplicates. **Fix:** moved duplicate-row removal to the end of the pipeline, after every column has been normalized.

## The duplicate-value detection heuristic (and why it needed fixing)

The first version flagged a column as "should be unique" only if it was >90% unique overall. This **failed on small datasets**: a column with duplicates naturally has a *lower* uniqueness ratio, so the presence of the exact duplicates we wanted to catch could push a column below its own detection threshold — self-defeating on anything but a large dataset.

**Fix:** any column whose name contains "id" (case-insensitive) is always checked for duplicates, regardless of its overall uniqueness ratio. Other columns still use the 90% threshold. This correctly catches things like a repeated `order_id` or `customer_id` even in a tiny test file.

## Output shape (what `clean` returns)

`clean` returns a report of what changed, not a profile. Example:

```json
{
  "original_row_count": 6,
  "duplicate_rows_removed": 1,
  "columns_cleaned": {
    "region": { "whitespace_trimmed": 1, "casing_standardized": 2 },
    "amount": { "missing_values_filled": 1 },
    "notes": { "blank_like_converted_to_null": 1, "whitespace_trimmed": 4, "missing_values_filled": 4 }
  },
  "final_row_count": 5,
  "file": "cleantest.csv",
  "output_file": "cleantest_cleaned.csv"
}
```

The legacy diagnosis-only `profile.py` (still in the codebase but no longer wired to a live command) returns a different, richer JSON shape describing the data without changing it:

```json
{
  "file": "sales.csv",
  "row_count": 8,
  "column_count": 5,
  "duplicate_column_names": [],
  "duplicate_rows": { "count": 1, "example_rows": [ ... ] },
  "columns": {
    "order_id": {
      "dtype": "int64",
      "null_count": 0,
      "null_percent": 0.0,
      "unique_count": 6,
      "mean": 3.5, "median": 3.5, "min": 1.0, "max": 6.0,
      "duplicate_values": {
        "duplicate_value_count": 2,
        "examples": { "2": 2, "5": 2 },
        "note": "This column looks like it should have unique values (an ID or similar), but repeats were found."
      }
    },
    "region": {
      "dtype": "str",
      "null_count": 0,
      "top_values": { "North": 2, "South": 2, "north": 2, "south": 1, "-": 1 },
      "blank_like_count": 1,
      "blank_like_note": "...",
      "inconsistent_casing_example": ["North", "north"]
    }
  }
}
```

The AI reading this output (per `commands/scan.md`'s instructions) presents it as a readable summary and is specifically told to call out `duplicate_rows`, `duplicate_column_names`, `duplicate_values`, `blank_like_count`, and `inconsistent_casing_example` as real data quality issues.

## Edge case handling (added 2026-08-30/31, pandexai@0.1.5)

Four edge cases are now handled gracefully instead of crashing or producing misleading output:

- **Empty file (0 bytes):** `loaders.py` checks file size before attempting to read and raises a clear error (`"This file is empty (0 bytes) - there is no data to profile."`).
- **Zero data rows (file has only a header):** `profile.py` returns a `"warning"` field instead of `"columns"` data, so the AI tells the user plainly rather than trying to summarize stats that don't exist.
- **All-null column:** any column where `null_percent` is exactly `100.0` gets `"all_values_null": true` plus a note suggesting the column may not be needed. Numeric stats correctly come back as `null` rather than erroring.
- **Non-UTF8 encoding:** `loaders.py` tries UTF-8 first; on `UnicodeDecodeError` it retries with latin-1 and returns an `"encoding_note"` string. This is common for CSVs exported from Excel on Windows. The AI is instructed to mention this to the user, since some special characters may not display perfectly under the latin-1 fallback.
