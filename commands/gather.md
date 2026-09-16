# gather

Combines two or more files (CSV, Excel, or JSON) into one organized file.

It looks for a column that genuinely connects the files - not just a
matching column name, but one where the actual VALUES overlap significantly
between files (e.g. both files have an "order_id" or "date" column with
real matching values). If a strong connection is found, it joins the files
together on that column. If no reliable connection is found, it keeps each
file as its own sheet inside one workbook instead of forcing an incorrect
join.

The original files are NEVER modified. A new results folder is created
named "<first-file-name>_gathered_results", containing "gathered.xlsx"
(with Excel AutoFilter on every sheet).

## How to run this command

1. Run: python scripts/gather.py <file1> <file2> [file3 ...]
   (use the project's .pandex/venv Python interpreter, not the system one)
2. The script prints a JSON report. Fields to look for:
   - mode: "joined" (files were combined into one table) or "linked_sheets"
     (no reliable shared column was found, so files were kept as separate
     sheets in the same workbook)
   - join_column / join_column_overlap_score: which column was used to
     join, and how strong the match was (present only when mode is "joined")
   - row_counts_per_file: how many rows each input file had
   - final_row_count: rows in the combined result (present when joined)
   - gathered_file: path to the output file (in a folder next to the first input file)
   - file_notes: present only if a file needed special handling. Per file it
     may contain encoding_note, or malformed_rows_skipped with
     malformed_row_numbers (lines with the wrong number of fields that were
     left out). Tell the user about these; they affect the combined result.
3. Do NOT recompute, estimate, or guess any of these numbers yourself.
   Present a clear summary: which files were combined, how (joined on
   which column, or kept as separate sheets and why), and where the result
   was saved.
4. Always make clear the original files were left untouched.

## Example

user runs: /pandex gather sales.xlsx cost.xlsx
-> python scripts/gather.py sales.xlsx cost.xlsx
-> if both files share a real "date" column with overlapping values:
   creates sales_gathered_results/gathered.xlsx, one sheet, joined on date
-> if no reliable shared column exists:
   creates sales_gathered_results/gathered.xlsx with two separate sheets
   (sales, cost), each with AutoFilter
-> present the JSON report as a readable summary
