# PandexAI — Commands

## Command namespace

All PandexAI commands live under a single namespace: `/pandex <subcommand> [file]`.

**Behavior rule (decided, applies to all current and future commands):**
- No filename given → operate on the last **gathered** dataset (see `gather` below).
- Filename given → operate on just that one file.

## `/pandex clean` — BUILT (renamed from `scan`, 2026-08-31)

**`scan` was renamed to `clean`.** The command now both diagnoses AND actively fixes data quality issues, rather than just reporting them. It profiles a file (column types, null percentage, unique counts, basic stats) and then applies real fixes — never modifying the original file.

**Supported file types:** `.csv`, `.xlsx`, `.xls`, `.json`

**Usage:**
```
/pandex clean sales.csv
/pandex clean sales.xlsx
/pandex clean sales.json
```

**What it does:**
- Removes exact duplicate rows
- Standardizes inconsistent casing within a column (e.g. `"North"` vs `"north"` → merged to whichever variant is more common)
- Converts "blank-like" text values that aren't standard nulls — empty strings, `"N/A"`, `"-"`, `"null"`, `"none"`, `"unknown"` — into real missing values
- Trims extra whitespace from text values
- **Normalizes date fields** (added 2026-08-31/09-01): if a column's values mostly look like dates — even in mixed formats like `2024-01-05`, `01/06/2024`, `Jan 7 2024` — they're all reformatted to a consistent `YYYY-MM-DD`. Skipped entirely for identifier-like columns to avoid false positives.
- **Standardizes known categories** (added 2026-08-31/09-01): columns made up entirely of recognized variants for one concept — `m`/`male`/`f`/`female`, `y`/`yes`/`n`/`no`, `t`/`true`/`f`/`false` — get mapped to the canonical spelled-out form (`Male`, `Yes`, `True`, etc.). Only triggers when *every* value in the column matches one known group, so it won't misfire on unrelated data.
- Fills missing values: **numeric columns get the column median**, **text columns get `"Unknown"`** (decided with the user — median chosen over mean since it's less skewed by outliers; "Unknown" chosen over most-common-value fill since it doesn't quietly overstate the dominant category)
- **Conflict detection** (added 2026-09-02): rows sharing the same ID but differing in other fields (e.g. same `customer_id` with a different `gender` or `amount`) are flagged separately as "conflicts" — these are genuinely different data, not formatting duplicates, so a human needs to decide which is correct.

**Output shape (results folder, not a single file):** `clean` creates a `<name>_cleaned_results/` folder next to the original file — **the original is never touched**. It always contains `cleaned.xlsx`, and additionally (only if applicable):
- `duplicates.xlsx` — exact duplicate rows (all copies), with a `reason` column
- `conflicts.xlsx` — same-ID rows with differing data, with a `reason` column listing which fields differ
- `missing_values.xlsx` — original rows that had some missing fields, with a `reason` column listing which fields were blank
- `empty_rows.xlsx` — rows that were completely blank

Every file (including `cleaned.xlsx` itself) is always saved as `.xlsx` with **Excel AutoFilter dropdowns** on every column and auto-sized column widths — regardless of what format the original input file was — so the user can filter/sort by region, date, gender, status, or any other column directly in Excel. This was an explicit late addition after the results-file mess was flagged (embedded commas in `reason` text were scrambling raw CSVs when opened by double-click) and after a direct request for filtering.

Prints a JSON report of exactly what changed, column by column, plus which output files were created.

**Explicitly NOT done (deferred):** measurement/unit standardization (e.g. kg vs lbs, cm vs inches). Auto-converting units risks silently corrupting real numbers if the unit is guessed wrong — deferred until there's real example data to design it safely against.

**Deliberate design choices:**
- Duplicate-row removal happens **last**, after all normalization — otherwise near-duplicate rows that only differ by casing or blank-value representation would be missed (this was an actual bug found and fixed during testing, see `04-Decision-Log.md`).
- Missing-value filling is **not** applied to identifier-like columns' duplicate values — `clean` doesn't decide which duplicate ID is "correct," it only removes exact duplicate rows and normalizes formatting. Deduplicating meaningfully different rows sharing an ID is left to the user's judgment.

**How it runs under the hood:** the AI reads `SKILL.md` and `commands/clean.md`, then runs `python scripts/clean.py <file>` using the project's `.pandex/venv` Python interpreter (never the system Python), and presents the resulting JSON report as a readable summary — the output filename and confirmation that the original was untouched are always called out explicitly.

## `/pandex gather` — BUILT (2026-09-02/03)

Combines two or more explicitly-named files (CSV, Excel, or JSON) into one organized file. Unlike `clean`, `gather` currently requires filenames — it does not scan the folder automatically (user's explicit choice when this was designed).

**Usage:**
```
/pandex gather sales.xlsx cost.xlsx
/pandex gather sales.csv cost.csv operating_cost.csv
```

**How it decides whether to join:** `gather` looks for a column that genuinely connects the files — not just a matching column name, but one where the actual VALUES overlap significantly between files. Column name matching alone is not enough (two unrelated files could both happen to have a `notes` or `region` column that means nothing to join on). The check:
1. Find column names shared (case-insensitively) across every file.
2. For each candidate, compute an overlap score: what fraction of each file's non-null values (normalized — trimmed, lowercased) also appear in every other file.
3. The candidate with the highest score, if it clears a minimum threshold (0.3), becomes the join column. A perfect match (e.g. the same order IDs in both files) scores 1.0.
4. If nothing clears the threshold, no column is trusted as a join key.

**Two possible outcomes:**

- **`mode: "joined"`** — a real shared column was found and trusted. The files are outer-joined on that column (so no rows from any file are dropped, even if one file has extra rows the others don't), suffixing overlapping non-key column names with the source filename to avoid collisions. Report includes `join_column` and `join_column_overlap_score`.

- **`mode: "linked_sheets"`** — no column had strong enough real value overlap across all files (even if column *names* happened to match). This is the deliberate safety fallback: `gather` refuses to guess a connection it isn't confident about, rather than silently producing a wrong merge. Instead of forcing a join:
  1. `gather` still creates one output file — `gathered.xlsx` — but instead of merging, it puts each input file on its own sheet inside that workbook (sheet named after the source file), each with its own AutoFilter.
  2. The JSON report's `reason` field explains why: `"No column with strong matching values was found across all files, so they were kept as separate sheets instead of forcing an incorrect join."`
  3. Nothing is merged or guessed — the datasets sit next to each other in one file for convenience, fully intact, ready for manual review or to be fed into `clean` separately.

  Verified directly: two files sharing column names (`region`, `notes`) but with completely different actual values (`North`/`South` vs `Alpha`/`Beta`) correctly triggered `linked_sheets` rather than a nonsense join — confirming the fallback isn't fooled by name-only coincidences.

**Output:** always a `<first-file-name>_gathered_results/gathered.xlsx`, with AutoFilter on every sheet. The original input files are never modified.

**Open question (not yet decided):** `gather` does not clean the input files first — if the inputs are messy (duplicates, blank placeholders, inconsistent casing outside the join column), the combined output will be messy too. The join-column matching itself is resilient to formatting noise (values are trimmed/lowercased before comparing), but nothing else is fixed. Current guidance given to the user: run `clean` on each file first, then `gather` the cleaned results, e.g.:
```
/pandex clean sales.csv
/pandex clean cost.csv
/pandex gather sales_cleaned_results\cleaned.xlsx cost_cleaned_results\cleaned.xlsx
```
Still undecided: whether `gather` should eventually run the cleaning pipeline on each file automatically before joining, so it "just works" on raw messy input without requiring the two-step manual flow. Revisit with the user.

**Built:** `scripts/gatherer.py` (shared-column detection + overlap scoring + join/link logic) + `scripts/gather.py` (entry point: load each file → gather → save `gathered.xlsx` → print JSON report). `commands/gather.md` written; `.claude/commands/pandex.md` updated to route the `gather` subcommand (previously said "planned but not built yet").

## `/pandex analyze` — PLANNED, NOT BUILT

Intended to go deeper than `clean`: correlations between columns, trends over time, group comparisons, patterns worth flagging — run against the gathered dataset or a specific file, same no-filename/filename rule as above.

## Future / idea-stage commands

Mapped from what a real data analyst's job actually involves:

| Analyst task | Command |
|---|---|
| Validate against business rules (e.g. "revenue should never be negative") | `/pandex validate` |
| Compare two datasets or time periods | `/pandex compare` |
| Find anomalies / outliers / sudden spikes | `/pandex anomalies` |

None of these are built yet. `clean` (formerly `scan`) was deliberately hardened first since every other command inherits its file-reading and data-quality-check foundations; `gather` was built next.

## The two "command file" mechanisms — don't confuse them

- `commands/clean.md` / `commands/gather.md` — plain instructions for an AI to read (works via a plain-language prompt like "read commands/clean.md and run clean").
- `.claude/commands/pandex.md` — the actual file that makes `/pandex <subcommand> [file]` work as a real typed command in Claude Code. This is what parses the subcommand and file argument(s) and routes to the right script.

See `01-Architecture.md` for the full story on why both exist and the packaging bug that once broke the second one silently.
