import re
import pandas as pd
import numpy as np

def standardize_casing(series):
    non_null = series.dropna().astype(str)
    if len(non_null) == 0:
        return series, 0

    counts = non_null.value_counts()
    lower_to_best = {}
    for val, count in counts.items():
        key = val.lower()
        if key not in lower_to_best or count > lower_to_best[key][1]:
            lower_to_best[key] = (val, count)

    replacements = {}
    changed_count = 0
    for val in non_null.unique():
        key = val.lower()
        best_val = lower_to_best[key][0]
        if val != best_val:
            replacements[val] = best_val
            changed_count += int((non_null == val).sum())

    if not replacements:
        return series, 0

    cleaned = series.apply(lambda v: replacements.get(v, v) if isinstance(v, str) else v)
    return cleaned, changed_count

BLANK_LIKE_VALUES = {"", "n/a", "na", "null", "none", "-", "nan", "unknown"}

def normalize_blank_like(series):
    def convert(v):
        if isinstance(v, str) and v.strip().lower() in BLANK_LIKE_VALUES:
            return np.nan
        return v
    converted = series.apply(convert)
    changed_count = int((converted.isna() & ~series.isna()).sum())
    return converted, changed_count

def trim_whitespace(series):
    def trim(v):
        if isinstance(v, str):
            return v.strip()
        return v
    trimmed = series.apply(trim)
    changed_count = 0
    for a, b in zip(series.tolist(), trimmed.tolist()):
        if a != b:
            changed_count += 1
    return trimmed, changed_count

KNOWN_CATEGORY_GROUPS = [
    {"m": "Male", "male": "Male", "f": "Female", "female": "Female"},
    {"y": "Yes", "yes": "Yes", "n": "No", "no": "No"},
    {"true": "True", "t": "True", "false": "False", "f": "False"},
]

def standardize_known_categories(series):
    non_null = series.dropna().astype(str)
    if len(non_null) == 0:
        return series, 0

    lowered_unique = set(v.strip().lower() for v in non_null.unique())
    if not lowered_unique:
        return series, 0

    for group in KNOWN_CATEGORY_GROUPS:
        if lowered_unique.issubset(group.keys()):
            def convert(v):
                if isinstance(v, str):
                    key = v.strip().lower()
                    if key in group:
                        return group[key]
                return v
            converted = series.apply(convert)
            changed_count = int((converted.astype(str) != series.astype(str)).sum())
            if changed_count:
                return converted, changed_count
            return series, 0

    return series, 0

DATE_LIKE_PATTERN = re.compile(
    r"\d{1,4}[-/]\d{1,2}[-/]\d{1,4}|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b",
    re.IGNORECASE
)

def standardize_dates(series, column_name):
    if "id" in column_name.lower():
        return series, 0

    non_null = series.dropna().astype(str)
    if len(non_null) == 0:
        return series, 0

    looks_like_dates = non_null.str.contains(DATE_LIKE_PATTERN, na=False).mean() >= 0.5
    if not looks_like_dates:
        return series, 0

    parsed = pd.to_datetime(non_null, errors="coerce", format="mixed")
    success_rate = parsed.notna().mean()
    if success_rate < 0.9:
        return series, 0

    def convert(v):
        if pd.isna(v):
            return v
        dt = pd.to_datetime(str(v), errors="coerce", format="mixed")
        if pd.isna(dt):
            return v
        return dt.strftime("%Y-%m-%d")

    converted = series.apply(convert)
    changed_count = int((converted.astype(str) != series.astype(str)).sum())
    return converted, changed_count

def fill_missing(series):
    null_count = int(series.isnull().sum())
    if null_count == 0:
        return series, 0

    if pd.api.types.is_numeric_dtype(series):
        fill_value = series.median()
        filled = series.fillna(fill_value)
        return filled, null_count
    else:
        filled = series.fillna("Unknown")
        return filled, null_count

def clean_dataframe(df):
    report = {
        "original_row_count": len(df),
        "columns_cleaned": {}
    }

    original_df = df.copy()
    working = df.copy()

    for col in working.columns:
        series = working[col]
        col_report = {}

        if not pd.api.types.is_numeric_dtype(series):
            series, blank_changed = normalize_blank_like(series)
            if blank_changed:
                col_report["blank_like_converted_to_null"] = blank_changed

            series, trim_changed = trim_whitespace(series)
            if trim_changed:
                col_report["whitespace_trimmed"] = trim_changed

            series, date_changed = standardize_dates(series, str(col))
            if date_changed:
                col_report["dates_standardized"] = date_changed

            series, category_changed = standardize_known_categories(series)
            if category_changed:
                col_report["categories_standardized"] = category_changed

            series, casing_changed = standardize_casing(series)
            if casing_changed:
                col_report["casing_standardized"] = casing_changed

        working[col] = series
        if col_report:
            report["columns_cleaned"][str(col)] = col_report

    is_empty_row = working.isna().all(axis=1)
    empty_rows_df = original_df[is_empty_row].copy()
    working = working[~is_empty_row].copy()
    original_df = original_df[~is_empty_row].copy()

    has_missing = working.isna().any(axis=1)
    missing_df = original_df[has_missing].copy()
    if len(missing_df) > 0:
        missing_columns_list = []
        for idx in missing_df.index:
            cols_missing = [str(c) for c in working.columns if pd.isna(working.loc[idx, c])]
            missing_columns_list.append(", ".join(cols_missing))
        missing_df.insert(0, "missing_columns", missing_columns_list)

    dedup_key = working.fillna("__PANDEX_NULL__")
    dup_mask = dedup_key.duplicated(keep=False)
    duplicates_df = original_df[dup_mask].copy()
    if len(duplicates_df) > 0:
        group_tuples = dedup_key[dup_mask].apply(lambda row: tuple(row), axis=1)
        unique_keys = {}
        group_ids = []
        next_id = 1
        for key in group_tuples:
            if key not in unique_keys:
                unique_keys[key] = next_id
                next_id += 1
            group_ids.append(unique_keys[key])
        duplicates_df.insert(0, "duplicate_group", group_ids)

    for col in working.columns:
        series, fill_changed = fill_missing(working[col])
        working[col] = series
        if fill_changed:
            col_report = report["columns_cleaned"].setdefault(str(col), {})
            col_report["missing_values_filled"] = fill_changed

    before = len(working)
    cleaned = working.drop_duplicates(keep="first").reset_index(drop=True)

    report["empty_rows_removed"] = int(is_empty_row.sum())
    report["rows_with_missing_values"] = int(len(missing_df))
    report["duplicate_rows_removed"] = before - len(cleaned)
    report["final_row_count"] = len(cleaned)

    return cleaned, report, duplicates_df, missing_df, empty_rows_df
