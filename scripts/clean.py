import sys
import os
import json
from loaders import load_dataframe
from cleaner import clean_dataframe

def build_output_path(path):
    base, ext = os.path.splitext(path)
    return f"{base}_cleaned{ext}"

def save_dataframe(df, path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        df.to_csv(path, index=False)
    elif ext in (".xlsx", ".xls"):
        df.to_excel(path, index=False)
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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: python clean.py <path-to-file>"}))
        sys.exit(1)

    file_path = sys.argv[1]
    try:
        result = clean_file(file_path)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
