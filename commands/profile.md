# profile

Diagnoses a CSV, Excel (.xlsx/.xls), or JSON file without changing it: read-only,
per-column statistics and data-quality signals. This is the fast, lightweight
look at a file - `analyze` builds on the same numbers and adds correlations,
trends, group comparisons, and outliers.

Nothing is written to disk. The original file is never modified, and no
results folder is created - this command only prints its JSON report.

Reports, per column: data type, null count/percent, unique value count, and
for numeric columns mean/median/min/max, or for text columns the top 5 most
common values. Also flags: columns that are entirely null, values that look
blank but aren't real nulls ("", "N/A", "-", etc. stored as text), inconsistent
casing ("North" vs "north"), and columns that look like an ID but have
duplicate values. Also reports duplicate row counts and duplicate column
names, if any.

## How to run this command

1. Run: python scripts/profile.py <path-to-file>
   (use the project's .pandex/venv Python interpreter, not the system one)
   Unlike `clean` and `gather`, `profile` currently requires a filename -
   it does not fall back to the last gathered file.
2. The script prints a JSON report. Fields to look for:
   - row_count, column_count, duplicate_column_names, duplicate_rows
   - columns: one entry per column with dtype, null_count, null_percent,
     unique_count, and (numeric) mean/median/min/max or (text) top_values
   - per-column: all_values_null (with a note), blank_like_count (with a
     note), inconsistent_casing_example, duplicate_values (with a note)
   - encoding_note / malformed_rows_skipped / malformed_row_numbers: present
     only if the file needed special handling. Tell the user about these.
3. Do NOT recompute, estimate, or guess any of these numbers yourself.
   Present a clear summary of the file's shape and any data-quality issues
   found. If the user seems to want deeper analysis (trends, correlations,
   comparisons between groups), suggest `/pandex analyze` instead.
4. If the output contains "warning" instead of column data, the file has no
   data rows - tell the user plainly rather than trying to summarize.

## Example

user runs: /pandex profile sales.csv
-> python scripts/profile.py sales.csv
-> prints a JSON report with row/column counts and per-column statistics
-> present it as a readable summary: shape of the file, any nulls/blanks/
   casing/duplicate issues found, and the top values in categorical columns
