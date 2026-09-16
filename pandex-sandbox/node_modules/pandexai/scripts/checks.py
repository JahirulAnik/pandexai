import pandas as pd

BLANK_LIKE_VALUES = {"", "n/a", "na", "null", "none", "-", "nan", "unknown"}


def duplicate_row_summary(df):
    dup_mask = df.duplicated(keep=False)
    dup_count = int(df.duplicated(keep="first").sum())
    if dup_count == 0:
        return {"count": 0}
    examples = df[dup_mask].head(3).to_dict(orient="records")
    return {"count": dup_count, "example_rows": examples}


def duplicate_value_summary(series, column_name, uniqueness_threshold=0.9, max_examples=3):
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


def count_blank_like(series):
    non_null = series.dropna().astype(str).str.strip().str.lower()
    return int(non_null.isin(BLANK_LIKE_VALUES).sum())


def check_inconsistent_casing(series):
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


def safe_float(value):
    try:
        if pd.isna(value):
            return None
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None
