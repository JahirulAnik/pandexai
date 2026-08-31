import re
import pandas as pd
import numpy as np

def standardize_casing(series):
    """For text columns, pick the most frequent casing variant for each
    lowercase value and replace all variants with it."""
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
    """Convert blank-like text values (empty string, 'N/A', '-', etc.) to real NaN."""
    def convert(v):
        if isinstance(v, str) and v.strip().lower() in BLANK_LIKE_VALUES:
            return np.nan
        return v
    converted = series.apply(convert)
    changed_count = int((converted.isna() & ~series.isna()).sum())
    return converted, changed_count


def trim_whitespace(series):
    """Strip leading/trailing whitespace from string values."""
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


# Known category groups: a column standardizes against a group only if EVERY
# non-null value (lowercased, stripped) falls inside that group's keys.
# This avoids misfiring on unrelated data - it only triggers when the whole
# column is clearly one of these concepts.
KNOWN_CATEGORY_GROUPS = [
    {"m": "Male", "male": "Male", "f": "Female", "female": "Female"},
    {"y": "Yes", "yes": "Yes", "n": "No", "no": "No"},
    {"true": "True", "t": "True", "false": "False", "f": "False"},
]

def standardize_known_categories(series):
    """Maps common abbreviations/variants (M/Male, Y/Yes, T/True, etc.) to a
    single canonical spelled-out form, but only when the ENTIRE column
    matches one known group."""
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
    """If a column's values mostly look like dates and parse successfully,
    reformats them all to a consistent YYYY-MM-DD form. Skipped entirely for
    identifier-like columns (name contains 'id') to avoid false positives."""
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
    """Fill missing values: median for numeric columns, 'Unknown' for text columns."""
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
    """Applies the full cleaning pipeline to a dataframe.
    Returns (cleaned_df, report dict)."""
    report = {
        "original_row_count": len(df),
        "duplicate_rows_removed": 0,
        "columns_cleaned": {}
    }

    for col in df.columns:
        series = df[col]
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

        series, fill_changed = fill_missing(series)
        if fill_changed:
            col_report["missing_values_filled"] = fill_changed

        df[col] = series

        if col_report:
            report["columns_cleaned"][str(col)] = col_report

    before = len(df)
    df = df.drop_duplicates(keep="first").reset_index(drop=True)
    report["duplicate_rows_removed"] = before - len(df)

    report["final_row_count"] = len(df)
    return df, report

