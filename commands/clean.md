# clean

Diagnoses AND cleans a CSV, Excel (.xlsx/.xls), or JSON file:
- Removes exact duplicate rows
- Standardizes inconsistent casing (e.g. "North" vs "north")
- Converts blank-like values ("", "N/A", "NULL", "?", "\N", "-", "--", "none") to real missing values
- Trims extra whitespace from text values
- Converts numeric columns that were stored as text (because of a "?" or similar) back to numbers
- Standardizes date columns to YYYY-MM-DD
- Standardizes known category values (M/Male/male -> Male, Y/Yes -> Yes, etc.)
- Fills missing values: numeric columns get the column median, text columns get "Unknown"

The original file is NEVER modified. Instead, a results folder is created
next to it, named "<name>_cleaned_results", containing:

- cleaned.xlsx        - the final cleaned data. Always .xlsx with AutoFilter
                        dropdowns on every column (region, date, gender,
                        status, etc.) and auto-sized column widths, so the
                        user can filter or sort directly in Excel regardless
                        of the original file's format. (always created)
- duplicates.xlsx     - only if exact duplicates were found. Has a "reason"
                        column explaining the match.
- conflicts.xlsx      - only if same-ID rows with differing data were found.
                        Has a "reason" column listing which fields differ.
- missing_values.xlsx - only if some rows had missing values. Has a "reason"
                        column listing which fields were blank.
- empty_rows.xlsx     - only if some rows were COMPLETELY blank.

All files have AutoFilter dropdowns and auto-sized columns.

## How to run this command

1. Run: python scripts/clean.py <path-to-file>
   (use the project's .pandex/venv Python interpreter, not the system one)
2. The script prints a JSON report. Fields to look for:
   - output_folder: the results folder that was created
   - cleaned_file: path to the main cleaned .xlsx file
   - duplicates_file / conflicts_file / missing_values_file / empty_rows_file:
     present only if that category had data
   - columns_cleaned: per-column details of what was changed. Possible keys:
     blank_like_converted_to_null, whitespace_trimmed, dates_standardized,
     categories_standardized, casing_standardized, converted_to_numeric,
     missing_values_filled
   - duplicate_rows_removed, conflicting_duplicate_rows,
     rows_with_missing_values, empty_rows_removed
   - malformed_rows_skipped / malformed_row_numbers: present only if some
     CSV lines had the wrong number of fields (usually an unquoted comma
     inside a value). Those lines were NOT included in the output.
3. Do NOT recompute, estimate, or guess any of these numbers yourself.
   Present a clear summary and list every file inside the results folder.
   Mention that cleaned.xlsx has AutoFilter dropdowns so the user can filter
   by region, date, or any other column directly in Excel.
4. Always make clear their original file was left untouched.
5. If the output contains "warning" instead of a report, the file has no
   data rows - tell the user plainly rather than trying to summarize.
6. If the output contains "encoding_note", mention the file wasn't standard
   UTF-8 and some characters might not display correctly.
7. If the output contains "malformed_rows_skipped", tell the user how many
   lines were skipped and give the line numbers so they can fix them in the
   original file. Do not describe the cleaned file as complete in that case.

## Example

user runs: /pandex clean sales.csv
-> python scripts/clean.py sales.csv
-> creates sales_cleaned_results/ containing cleaned.xlsx (with AutoFilter)
   and, if applicable, duplicates.xlsx, conflicts.xlsx, missing_values.xlsx,
   empty_rows.xlsx
-> present the JSON report as a readable summary, listing every file created
