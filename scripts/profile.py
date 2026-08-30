import sys
import json
import pandas as pd

# Values that mean "missing" even though pandas won't catch them as NaN by default
BLANK_LIKE_VALUES = {"", "n/a", "na", "null", "none", "-", "nan", "unknown"}


def profile_csv(path):
    # First, check the raw header row for duplicate column names before pandas
    # silently renames them (e.g. "amount" and "amount" become "amount" and "amount.1")
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        raw_header = f.readline().strip().split(",")
    seen = {}
    duplicate_column_names = []
    for name in raw_header:
        seen[name] = seen.get(name, 0) + 1
        if seen[name] == 2:
            duplicate_column_names.append(name)

    df = pd.read_csv(path)

    result = {
        "file": path,
        "row_count": len(df),
        "column_count": len(df.columns),
        "duplicate_column_names": duplicate_column_names,
        "duplicate_rows": _duplicate_row_summary(df),
        "columns": {}
    }

    for col in df.columns:
        series = df[col]
        col_info = {
            "dtype": str(series.dtype),
            "null_count": int(series.isnull().sum()),
            "null_percent": round(float(series.isnull().mean() * 100), 2),
            "unique_count": int(series.nunique())
        }

        if pd.api.types.is_numeric_dtype(series):
            col_info["mean"] = _safe_float(series.mean())
            col_info["median"] = _safe_float(series.median())
            col_info["min"] = _safe_float(series.min())
            col_info["max"] = _safe_float(series.max())
        else:
            top_values = series.value_counts().head(5)
            col_info["top_values"] = {str(k): int(v) for k, v in top_values.items()}

            blank_like_count = _count_blank_like(series)
            if blank_like_count > 0:
                col_info["blank_like_count"] = blank_like_count
                col_info["blank_like_note"] = (
                    "Values like empty strings, 'N/A', '-', or 'null' as text were found. "
                    "These are not counted in null_count above but likely represent missing data."
                )

            inconsistent_casing = _check_inconsistent_casing(series)
            if inconsistent_casing:
                col_info["inconsistent_casing_example"] = inconsistent_casing

        dup_check = _duplicate_value_summary(series, col)
        if dup_check:
            col_info["duplicate_values"] = dup_check

        result["columns"][col] = col_info

    return result


def _duplicate_row_summary(df):
    dup_mask = df.duplicated(keep=False)
    dup_count = int(df.duplicated(keep="first").sum())
    if dup_count == 0:
        return {"count": 0}
    examples = df[dup_mask].head(3).to_dict(orient="records")
    return {"count": dup_count, "example_rows": examples}


def _duplicate_value_summary(series, column_name, uniqueness_threshold=0.9, max_examples=3):
    non_null = series.dropna()
    if len(non_null) == 0:
        return None
    uniqueness_ratio = non_null.nunique() / len(non_null)
    looks_like_id = "id" in column_name.lower()
    if not looks_like_id and uniqueness_ratio < uniqueness_threshold:
        return None
    value_counts = non_null.value_counts()
    duplicated_values = value_counts[value_counts > 1]
    if len(duplicated_values) == 0:
        return None
    return {
        "duplicate_value_count": int(duplicated_values.sum() - len(duplicated_values)),
        "examples": {str(k): int(v) for k, v in duplicated_values.head(max_examples).items()},
        "note": "This column looks like it should have unique values (an ID or similar), but repeats were found."
    }


def _count_blank_like(series):
    non_null = series.dropna().astype(str).str.strip().str.lower()
    return int(non_null.isin(BLANK_LIKE_VALUES).sum())


def _check_inconsistent_casing(series):
    non_null = series.dropna().astype(str)
    if len(non_null) == 0:
        return None
    original_unique = non_null.nunique()
    lowered_unique = non_null.str.lower().nunique()
    if lowered_unique < original_unique:
        lower_to_variants = {}
        for val in non_null.unique():
            key = val.lower()
            lower_to_variants.setdefault(key, set()).add(val)
        for key, variants in lower_to_variants.items():
            if len(variants) > 1:
                return sorted(variants)
    return None


def _safe_float(value):
    try:
        if pd.isna(value):
            return None
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: python profile.py <path-to-csv>"}))
        sys.exit(1)

    csv_path = sys.argv[1]
    try:
        profile = profile_csv(csv_path)
        print(json.dumps(profile, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
