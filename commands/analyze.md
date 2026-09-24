# analyze

The full read-only analysis of a CSV, Excel (.xlsx/.xls), or JSON file: every
per-column statistic `profile` reports, plus everything else a data analyst
would want to check next. Nothing is written to disk and the original file is
never modified - like `profile`, this command only prints its JSON report.

If no filename is given, it falls back to whatever `/pandex gather` most
recently produced in this project (the same chaining behavior `clean` has),
so `gather` then `analyze` with no arguments works.

Covers, automatically and deterministically:
- Everything `profile` reports: per-column stats, blank-like values,
  inconsistent casing, duplicate rows/values. See commands/profile.md.
- **Correlations**: every pair of numeric columns, Pearson correlation,
  strongest pairs first. ID-like columns are excluded (a correlation with a
  row number is never meaningful).
- **Trends over time**: only if a date-like column was found. Rows are
  bucketed into an auto-picked period (day/week/month/year, based on how much
  time the data spans) and every numeric column's first-period vs last-period
  average is reported, with a direction (increasing/decreasing/flat) and
  percent change.
- **Group comparisons**: for every column that looks categorical (a handful
  of repeated values - not free text, not an ID), the average of every
  numeric column broken out by group (e.g. "average order value by region"),
  with the highest- and lowest-scoring group called out.
- **Outliers**: classic IQR fences (1.5x the interquartile range beyond the
  25th/75th percentile) per numeric column, with the count, percent of rows
  affected, the normal range, and a few example values.

## How to run this command

1. Run: python scripts/analyze.py <path-to-file>
   or, with no filename, to analyze whatever gather last produced:
   python scripts/analyze.py
   (use the project's .pandex/venv Python interpreter, not the system one)
2. The script prints a JSON report. Fields to look for, beyond everything
   profile.md already lists:
   - correlations: a list of {column_a, column_b, correlation, strength}.
     Empty list if fewer than two numeric columns exist. "strength" is a
     plain-English label like "strong positive" or "weak negative".
   - trends: null if no usable date column was found (say so plainly rather
     than inventing a trend). Otherwise: date_column, period ("day"/"week"/
     "month"/"year"), period_count, date_range, and columns - a per-numeric-
     column first/last period average, percent_change, and direction.
   - group_comparisons: a list of {group_by, metric, group_averages,
     highest, lowest}. Empty list if no suitable categorical column or no
     numeric columns exist.
   - outliers: a dict keyed by column name, each with outlier_count,
     outlier_percent, normal_range, and example_values. Only columns with at
     least one outlier are included - an empty dict means none were found.
   - used_last_gathered_file: present only when no filename was given - the
     file analyze picked up automatically. Tell the user which file this was.
3. Do NOT recompute, estimate, or guess any of these numbers yourself.
4. Present a clear, prioritized summary - don't just dump every field. Lead
   with whatever is most actionable: a strong correlation, a clear trend, a
   big gap between groups, or a column with a lot of outliers. Explicitly
   say when a section came back empty (no date column found for trends, no
   numeric columns for correlations, etc.) rather than skipping it silently.
5. If the output contains "warning" instead of a report, the file has no
   data rows - tell the user plainly rather than trying to summarize.

## Example

user runs: /pandex analyze orders.csv
-> python scripts/analyze.py orders.csv
-> prints column stats, correlations, a trend over the date column found (if
   any), group comparisons by category columns, and any outliers
-> present the most useful findings first, in plain English, and note any
   section that came back empty and why

user runs: /pandex gather orders.csv customers.csv
user runs: /pandex analyze (no filename)
-> python scripts/analyze.py
-> analyzes whatever gather just combined
-> tell the user which file this was, since they didn't type it themselves
