import os
import pandas as pd


def load_dataframe(path):
    """Reads a CSV, Excel, or JSON file into a pandas DataFrame.
    Returns (dataframe, list_of_duplicate_column_names, encoding_note)."""
    ext = os.path.splitext(path)[1].lower()
    encoding_note = None

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
            encoding_note = (
                "This file is not standard UTF-8 text (common with CSVs exported from Excel). "
                "It was read using latin-1 encoding instead. Some special characters may not "
                "display correctly."
            )

        duplicate_column_names = _find_duplicates(raw_header)

        try:
            df = pd.read_csv(path, encoding=encoding_used)
        except pd.errors.EmptyDataError:
            raise ValueError("This file has no columns or rows - there is no data to profile.")

        return df, duplicate_column_names, encoding_note

    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(path)
        if df.empty and len(df.columns) == 0:
            raise ValueError("This file has no columns or rows - there is no data to profile.")
        return df, _find_duplicates(df.columns), None

    elif ext == ".json":
        df = pd.read_json(path)
        if df.empty and len(df.columns) == 0:
            raise ValueError("This file has no columns or rows - there is no data to profile.")
        return df, _find_duplicates(df.columns), None

    else:
        raise ValueError(
            f"Unsupported file type '{ext}'. PandexAI currently supports .csv, .xlsx, .xls, and .json files."
        )


def _find_duplicates(names):
    seen = {}
    duplicates = []
    for name in names:
        seen[name] = seen.get(name, 0) + 1
        if seen[name] == 2:
            duplicates.append(name)
    return duplicates
