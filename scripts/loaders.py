import os
import pandas as pd


def load_dataframe(path):
    """Reads a CSV, Excel, or JSON file into a pandas DataFrame.
    Returns (dataframe, list_of_duplicate_column_names)."""
    ext = os.path.splitext(path)[1].lower()

    if ext == ".csv":
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            raw_header = f.readline().strip().split(",")
        duplicate_column_names = _find_duplicates(raw_header)
        df = pd.read_csv(path)
        return df, duplicate_column_names

    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(path)
        return df, _find_duplicates(df.columns)

    elif ext == ".json":
        df = pd.read_json(path)
        return df, _find_duplicates(df.columns)

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
