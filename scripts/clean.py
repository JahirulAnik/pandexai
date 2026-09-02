import sys
import os
import json
import pandas as pd
from loaders import load_dataframe
from cleaner import clean_dataframe

def build_output_folder(path):
    base, _ext = os.path.splitext(path)
    folder = f"{base}_cleaned_results"
    os.makedirs(folder, exist_ok=True)
    return folder

def add_excel_autofilter(path, row_count, column_count):
    from openpyxl import load_workbook
    from openpyxl.utils import get_column_letter

    workbook = load_workbook(path)
    worksheet = workbook.active

    last_column_letter = get_column_letter(column_count)
    last_row = row_count + 1
    worksheet.auto_filter.ref = f"A1:{last_column_letter}{last_row}"

    for col_idx, col_name in enumerate(worksheet[1], start=1):
        max_length = max(
            [len(str(col_name.value))] +
            [len(str(cell.value)) for cell in worksheet[get_column_letter(col_idx)][1:200] if cell.value is not None]
        )
        worksheet.column_dimensions[get_column_letter(col_idx)].width = min(max_length + 2, 60)

    workbook.save(path)

def save_dataframe(df, path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        df.to_csv(path, index=False)
    elif ext in (".xlsx", ".xls"):
        df.to_excel(path, index=False)
        add_excel_autofilter(path, len(df), len(df.columns))
    elif ext == ".json":
        df.to_json(path, orient="records", indent=2)
    else:
        raise ValueError(f"Unsupported file type '{ext}' for saving.")

def clean_file(path):
    df, duplicate_column_names, encoding_note = load_dataframe(path)

    if len(df) == 0:
        return {
            "file": path,
            "warning": "This file has columns but zero data rows - nothing to clean."
        }

    _base, ext = os.path.splitext(path)
    cleaned_df, report, duplicates_df, missing_df, empty_rows_df, conflicts_df = clean_dataframe(df)

    output_folder = build_output_folder(path)

    # The main cleaned file keeps the original format (so it drops into the
    # same pipeline the user already has). The review files (duplicates,
    # conflicts, missing values, empty rows) are always saved as .xlsx with
    # AutoFilter and auto-sized columns, since they're meant for a human to
    # open and review in Excel - this avoids the raw-CSV display mess.
    cleaned_path = os.path.join(output_folder, f"cleaned{ext}")
    save_dataframe(cleaned_df, cleaned_path)
    report["file"] = path
    report["output_folder"] = output_folder
    report["cleaned_file"] = cleaned_path

    if len(duplicates_df) > 0:
        duplicates_path = os.path.join(output_folder, "duplicates.xlsx")
        save_dataframe(duplicates_df, duplicates_path)
        report["duplicates_file"] = duplicates_path

    if len(conflicts_df) > 0:
        conflicts_path = os.path.join(output_folder, "conflicts.xlsx")
        save_dataframe(conflicts_df, conflicts_path)
        report["conflicts_file"] = conflicts_path

    if len(missing_df) > 0:
        missing_path = os.path.join(output_folder, "missing_values.xlsx")
        save_dataframe(missing_df, missing_path)
        report["missing_values_file"] = missing_path

    if len(empty_rows_df) > 0:
        empty_path = os.path.join(output_folder, "empty_rows.xlsx")
        save_dataframe(empty_rows_df, empty_path)
        report["empty_rows_file"] = empty_path

    if duplicate_column_names:
        report["duplicate_column_names_found"] = duplicate_column_names
    if encoding_note:
        report["encoding_note"] = encoding_note

    return report

def friendly_error_message(e, path):
    if isinstance(e, FileNotFoundError):
        return f"Couldn't find a file at '{path}'. Check the file name and make sure it's in this folder."

    if isinstance(e, PermissionError):
        return f"Couldn't open '{path}' - it might be open in another program (like Excel). Close it and try again."

    if isinstance(e, pd.errors.EmptyDataError):
        return "This file has no columns or rows - there is no data to clean."

    if isinstance(e, pd.errors.ParserError):
        return f"'{path}' doesn't look like a valid, well-formed file. It may be corrupted or use an unusual format."

    if isinstance(e, UnicodeDecodeError):
        return f"Couldn't read the text in '{path}' - it may use an unusual character encoding."

    if isinstance(e, IsADirectoryError):
        return f"'{path}' is a folder, not a file. Point this at a specific file instead."

    message = str(e)
    lower_message = message.lower()
    if "zip file" in lower_message or "not a zip file" in lower_message or "file format cannot be determined" in lower_message or "engine manually" in lower_message:
        return f"'{path}' doesn't look like a valid Excel file. It may be corrupted or actually a different file type with a .xlsx extension."
    if "expecting value" in lower_message or "json" in lower_message:
        return f"'{path}' doesn't look like valid JSON. Check the file's formatting."

    return message

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: python clean.py <path-to-file>"}))
        sys.exit(1)

    file_path = sys.argv[1]
    try:
        result = clean_file(file_path)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": friendly_error_message(e, file_path)}))
        sys.exit(1)
