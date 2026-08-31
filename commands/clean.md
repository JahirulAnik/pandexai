# clean

Diagnoses AND cleans a CSV, Excel (.xlsx/.xls), or JSON file:
- Removes exact duplicate rows
- Standardizes inconsistent casing (e.g. "North" vs "north")
- Converts blank-like values ("", "N/A", "-", "null", "none") to real missing values
- Trims extra whitespace from text values
- Fills missing values: numeric columns get the column median, text columns get "Unknown"

The original file is NEVER modified. A new file is created alongside it with
"_cleaned" added to the name (e.g. sales.csv -> sales_cleaned.csv).

## How to run this command

1. Run: python scripts/clean.py <path-to-file>
   (use the project's .pandex/venv Python interpreter, not the system one)
2. The script prints a JSON report of exactly what was changed - duplicate
   rows removed, and per-column details (blank_like_converted_to_null,
   whitespace_trimmed, casing_standardized, missing_values_filled).
3. Do NOT recompute, estimate, or guess any of these numbers yourself.
   Present the report to the user in a clear, readable summary.
4. Always tell the user the name of the output file that was created, and
   make clear their original file was left untouched.
5. If the output contains "warning" instead of a report, the file has no
   data rows - tell the user plainly rather than trying to summarize.
6. If the output contains "encoding_note", mention the file wasn't standard
   UTF-8 and some characters might not display correctly.

## Example

user runs: /pandex clean sales.csv
-> python scripts/clean.py sales.csv
-> creates sales_cleaned.csv
-> present the resulting JSON report as a readable summary

Also works with sales.xlsx or sales.json the same way.
