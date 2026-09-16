import os

import pandas as pd


def load_dataframe(path):
    """Reads a CSV, Excel, or JSON file into a pandas DataFrame.
    Returns (dataframe, list_of_duplicate_column_names, notes) where notes is a
    dict that may contain:
      encoding_note            - the file was not UTF-8 and was read as latin-1
      malformed_rows_skipped   - number of CSV lines with the wrong number of fields
      malformed_row_numbers    - their 1-based line numbers (first 20)
    """
    ext = os.path.splitext(path)[1].lower()
    notes = {}

    if ext == ".csv":
        if os.path.getsize(path) == 0:
            raise ValueError("This file is empty (0 bytes) - there is no data to profile.")

        encoding_used = "utf-8"
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_header = f.readline().strip().split(",")
        except UnicodeDecodeError:
            encoding_used = "latin-1"
            with open(path, "r", encoding="latin-1") as f:
                raw_header = f.readline().strip().split(",")
            notes["encoding_note"] = (
                "This file is not standard UTF-8 text (common with CSVs exported from Excel). "
                "It was read using latin-1 encoding instead. Some special characters may not "
                "display correctly."
            )

        duplicate_column_names = _find_duplicates(raw_header)

        try:
            df = pd.read_csv(path, encoding=encoding_used)
        except pd.errors.EmptyDataError:
            raise ValueError("This file has no columns or rows - there is no data to profile.")
        except pd.errors.ParserError:
            df, bad_rows = _read_csv_skipping_malformed_rows(path, encoding_used)
            notes["malformed_rows_skipped"] = len(bad_rows)
            notes["malformed_row_numbers"] = bad_rows[:20]

        return df, duplicate_column_names, notes

    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(path)
        if df.empty and len(df.columns) == 0:
            raise ValueError("This file has no columns or rows - there is no data to profile.")
        return df, _find_duplicates(df.columns), notes

    elif ext == ".json":
        df = pd.read_json(path)
        if df.empty and len(df.columns) == 0:
            raise ValueError("This file has no columns or rows - there is no data to profile.")
        return df, _find_duplicates(df.columns), notes

    else:
        raise ValueError(
            f"Unsupported file type '{ext}'. PandexAI currently supports .csv, .xlsx, .xls, and .json files."
        )


def _read_csv_skipping_malformed_rows(path, encoding):
    """Real-world CSVs often have a few lines with an unquoted comma inside a
    value. Rather than refusing the whole file, read it again skipping those
    lines and report their line numbers so the user can fix them by hand."""
    df = pd.read_csv(path, encoding=encoding, engine="python", on_bad_lines=_drop_line)
    # pandas doesn't tell the callback which line it skipped, so find them with csv.reader.
    bad_rows = _locate_bad_lines(path, encoding, len(df.columns))
    return df, bad_rows


def _drop_line(_fields):
    return None


def _locate_bad_lines(path, encoding, expected_fields):
    import csv

    bad = []
    with open(path, "r", encoding=encoding, newline="") as f:
        reader = csv.reader(f)
        for line_number, row in enumerate(reader, start=1):
            if line_number == 1 or not row:
                continue
            if len(row) != expected_fields:
                bad.append(line_number)
    return bad


def _find_duplicates(names):
    seen = {}
    duplicates = []
    for name in names:
        seen[name] = seen.get(name, 0) + 1
        if seen[name] == 2:
            duplicates.append(name)
    return duplicates
