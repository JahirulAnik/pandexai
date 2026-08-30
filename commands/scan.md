# scan

Profiles a CSV, Excel (.xlsx/.xls), or JSON file: column types, null percentage,
unique counts, and basic stats (mean/median/min/max for numeric columns, top
value counts for categorical columns).

## How to run this command

1. Run: python scripts/profile.py <path-to-file>
   (use the project's .pandex/venv Python interpreter, not the system one)
2. The script prints a JSON object with the profiling results.
3. Do NOT recompute, estimate, or guess any of these numbers yourself.
   Present the JSON results to the user in a clear, readable summary, and
   flag anything that looks like a data quality issue (e.g. high null %,
   suspicious types, low-cardinality columns that might be categorical).
4. Pay special attention to duplicate_rows, duplicate_column_names,
   duplicate_values, blank_like_count, and inconsistent_casing_example in
   the output - these represent real data quality problems the user should
   know about before doing any analysis.
5. If the output contains "warning" instead of "columns" data, the file has
   no data rows - tell the user plainly rather than trying to summarize stats.
6. If a column has "all_values_null": true, call that out clearly - it means
   the entire column is empty and may not be worth keeping.
7. If the output contains "encoding_note", mention to the user that the file
   wasn't standard UTF-8 and some characters might not display correctly -
   this is common with CSVs exported from Excel on Windows.

## Example

user runs: /pandex scan sales.csv
-> python scripts/profile.py sales.csv
-> present the resulting JSON as a readable summary

Also works with sales.xlsx or sales.json the same way.
