import sys
import json
import pandas as pd
from loaders import load_dataframe
from checks import (
    duplicate_row_summary,
    duplicate_value_summary,
    count_blank_like,
    check_inconsistent_casing,
    safe_float,
)


def profile_file(path):
    df, duplicate_column_names, encoding_note = load_dataframe(path)

    if len(df) == 0:
        return {
            "file": path,
            "row_count": 0,
            "column_count": len(df.columns),
            "warning": "This file has columns but zero data rows - there is nothing to profile yet.",
            "columns": {}
        }

    result = {
        "file": path,
        "row_count": len(df),
        "column_count": len(df.columns),
        "duplicate_column_names": duplicate_column_names,
        "duplicate_rows": duplicate_row_summary(df),
        "columns": {}
    }

    if encoding_note:
        result["encoding_note"] = encoding_note

    for col in df.columns:
        series = df[col]
        col_info = {
            "dtype": str(series.dtype),
            "null_count": int(series.isnull().sum()),
            "null_percent": round(float(series.isnull().mean() * 100), 2),
            "unique_count": int(series.nunique())
        }

        if col_info["null_percent"] == 100.0:
            col_info["all_values_null"] = True
            col_info["note"] = "Every value in this column is missing. Consider whether this column is still needed."

        if pd.api.types.is_numeric_dtype(series):
            col_info["mean"] = safe_float(series.mean())
            col_info["median"] = safe_float(series.median())
            col_info["min"] = safe_float(series.min())
            col_info["max"] = safe_float(series.max())
        else:
            top_values = series.value_counts().head(5)
            col_info["top_values"] = {str(k): int(v) for k, v in top_values.items()}

            blank_like_count = count_blank_like(series)
            if blank_like_count > 0:
                col_info["blank_like_count"] = blank_like_count
                col_info["blank_like_note"] = (
                    "Values like empty strings, 'N/A', '-', or 'null' as text were found. "
                    "These are not counted in null_count above but likely represent missing data."
                )

            inconsistent_casing = check_inconsistent_casing(series)
            if inconsistent_casing:
                col_info["inconsistent_casing_example"] = inconsistent_casing

        dup_check = duplicate_value_summary(series, str(col))
        if dup_check:
            col_info["duplicate_values"] = dup_check

        result["columns"][str(col)] = col_info

    return result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: python profile.py <path-to-file>"}))
        sys.exit(1)

    file_path = sys.argv[1]
    try:
        profile = profile_file(file_path)
        print(json.dumps(profile, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
