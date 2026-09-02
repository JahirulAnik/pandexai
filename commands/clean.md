# clean

Diagnoses AND cleans a CSV, Excel (.xlsx/.xls), or JSON file:
- Removes exact duplicate rows
- Standardizes inconsistent casing (e.g. "North" vs "north")
- Converts blank-like values ("", "N/A", "-", "null", "none") to real missing values
- Trims extra whitespace from text values
- Standardizes date columns to YYYY-MM-DD
- Standardizes known category values (M/Male/male -> Male, Y/Yes -> Yes, etc.)
- Fills missing values: numeric columns get the column median, text columns get "Unknown"

The original file is NEVER modified. Instead, a results folder is created
next to it, named "<name>_cleaned_results", containing:

- cleaned.<ext>         - the final cleaned data (always created)
- duplicates.<ext>      - only if duplicates were found. Every row involved
                          in a duplicate (all copies), tagged with a
                          "duplicate_group" number so matching rows are clear.
- missing_values.<ext>  - only if some rows had missing values. Original
                          rows (before filling), tagged with a
                          "missing_columns" column listing which fields were blank.
- empty_rows.<ext>      - only if some rows were COMPLETELY blank.

All Excel files include AutoFilter dropdowns on the header row.

## How to run this command

1. Run: python scripts/clean.py <path-to-file>
   (use the project's .pandex/venv Python interpreter, not the system one)
2. The script prints a JSON report. Fields to look for:
   - output_folder: the results folder that was created
   - cleaned_file: path to the main cleaned file
   - duplicates_file / missing_values_file / empty_rows_file: present only
     if that category had data
   - columns_cleaned: per-column details of what was changed
   - duplicate_rows_removed, rows_with_missing_values, empty_rows_removed
3. Do NOT recompute, estimate, or guess any of these numbers yourself.
   Present a clear summary and list every file inside the results folder.
4. Always make clear their original file was left untouched.
5. If the output contains "warning" instead of a report, the file has no
   data rows - tell the user plainly rather than trying to summarize.
6. If the output contains "encoding_note", mention the file wasn't standard
   UTF-8 and some characters might not display correctly.

## Example

user runs: /pandex clean sales.xlsx
-> python scripts/clean.py sales.xlsx
-> creates sales_cleaned_results/ containing cleaned.xlsx and, if applicable,
   duplicates.xlsx, missing_values.xlsx, empty_rows.xlsx
-> present the JSON report as a readable summary, listing every file created
