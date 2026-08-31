import sys
import os
import json
import pandas as pd
from loaders import load_dataframe
from cleaner import clean_dataframe

def build_output_path(path):
    base, ext = os.path.splitext(path)
    return f"{base}_cleaned{ext}"

def add_excel_autofilter(path, row_count, column_count):
    """Adds Excel's AutoFilter dropdowns to the header row, so the user can
    sort ascending/descending or filter to specific values directly in Excel."""
    from openpyxl import load_workbook
    from openpyxl.utils import get_column_letter

    workbook = load_workbook(path)
    worksheet = workbook.active

    last_column_letter = get_column_letter(column_count)
    last_row = row_count + 1
    worksheet.auto_filter.ref = f"A1:{last_column_letter}{last_row}"

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

    cleaned_df, report = clean_dataframe(df)

    output_path = build_output_path(path)
    save_dataframe(cleaned_df, output_path)

    report["file"] = path
    report["output_file"] = output_path
    if duplicate_column_names:
        report["duplicate_column_names_found"] = duplicate_column_names
    if encoding_note:
        report["encoding_note"] = encoding_note

    return report


def friendly_error_message(e, path):
    """Translates common exceptions into plain-English messages."""
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
