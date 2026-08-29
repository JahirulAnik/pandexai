# scan

Profiles a CSV file: column types, null percentage, unique counts, and
basic stats (mean/median/min/max for numeric columns, top value counts for
categorical columns).

## How to run this command

1. Run: python scripts/profile.py <path-to-csv>
   (use the project's .pandex/venv Python interpreter, not the system one)
2. The script prints a JSON object with the profiling results.
3. Do NOT recompute, estimate, or guess any of these numbers yourself.
   Present the JSON results to the user in a clear, readable summary, and
   flag anything that looks like a data quality issue (e.g. high null %,
   suspicious types, low-cardinality columns that might be categorical).

## Example

user runs: /pandex scan sales.csv
-> python scripts/profile.py sales.csv
-> present the resulting JSON as a readable summary
