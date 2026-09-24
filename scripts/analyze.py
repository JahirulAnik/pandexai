import json
import os
import sys
from profile import profile_file

import pandas as pd
from clean import friendly_error_message, resolve_input_path
from cleaner import DATE_LIKE_PATTERN, is_id_column
from loaders import load_dataframe

# Caps keep the JSON report readable on wide/high-cardinality real data instead
# of dumping every possible pair or group.
MAX_CORRELATIONS_REPORTED = 15
MAX_GROUP_COLUMNS_REPORTED = 5
MAX_GROUPS_PER_COLUMN = 8
MAX_OUTLIER_EXAMPLES = 5
STRONG_CORRELATION_THRESHOLD = 0.5


def detect_date_columns(df):
    """Which columns look like, and mostly parse as, dates - without changing
    any data (clean.py owns actual date standardization). Reuses the same
    "looks like a date" pattern and 90% parse-success threshold as
    cleaner.standardize_dates, so analyze agrees with what clean would do."""
    date_columns = []
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_datetime64_any_dtype(series):
            date_columns.append(col)
            continue
        if pd.api.types.is_numeric_dtype(series):
            continue
        non_null = series.dropna().astype(str)
        if len(non_null) == 0:
            continue
        looks_like_dates = non_null.str.contains(DATE_LIKE_PATTERN, na=False).mean() >= 0.5
        if not looks_like_dates:
            continue
        parsed = pd.to_datetime(non_null, errors="coerce", format="mixed")
        if parsed.notna().mean() >= 0.9:
            date_columns.append(col)
    return date_columns


def _correlation_strength(r):
    magnitude = abs(r)
    if magnitude >= 0.7:
        label = "strong"
    elif magnitude >= STRONG_CORRELATION_THRESHOLD:
        label = "moderate"
    else:
        label = "weak"
    direction = "positive" if r >= 0 else "negative"
    return f"{label} {direction}"


def compute_correlations(df):
    """Pairwise Pearson correlation between every pair of numeric columns
    (ID-like columns excluded - a correlation with a row-number-like ID is
    never meaningful). Returns the strongest pairs, most correlated first."""
    numeric_cols = [c for c in df.select_dtypes(include="number").columns if not is_id_column(c)]
    if len(numeric_cols) < 2:
        return []

    corr_matrix = df[numeric_cols].corr(numeric_only=True)
    pairs = []
    for i, col_a in enumerate(numeric_cols):
        for col_b in numeric_cols[i + 1:]:
            r = corr_matrix.loc[col_a, col_b]
            if pd.isna(r):
                continue
            pairs.append({
                "column_a": str(col_a),
                "column_b": str(col_b),
                "correlation": round(float(r), 4),
                "strength": _correlation_strength(r),
            })

    pairs.sort(key=lambda p: abs(p["correlation"]), reverse=True)
    return pairs[:MAX_CORRELATIONS_REPORTED]


def _pick_trend_period(span_days):
    if span_days >= 730:
        return "Y", "year"
    if span_days >= 90:
        return "M", "month"
    if span_days >= 14:
        return "W", "week"
    return "D", "day"


def compute_trends(df, date_columns):
    """If a date column was found, buckets rows into an auto-picked period
    (day/week/month/year, based on how much time the data spans) and reports
    the first-vs-last period average for every numeric column, so a trend
    ("revenue is increasing") is visible without the AI eyeballing raw rows."""
    if not date_columns:
        return None

    numeric_cols = [c for c in df.select_dtypes(include="number").columns if not is_id_column(c)]
    if not numeric_cols:
        return None

    date_col = date_columns[0]
    parsed_dates = pd.to_datetime(df[date_col], errors="coerce", format="mixed")
    valid = parsed_dates.notna()
    if valid.sum() < 2:
        return None

    span_days = (parsed_dates[valid].max() - parsed_dates[valid].min()).days
    period, period_label = _pick_trend_period(span_days)

    working = df.loc[valid, numeric_cols].copy()
    working["__period__"] = parsed_dates[valid].dt.to_period(period)
    grouped = working.groupby("__period__", observed=True)[numeric_cols].mean().sort_index()
    if len(grouped) < 2:
        return None

    columns = {}
    for col in numeric_cols:
        first_value = grouped[col].iloc[0]
        last_value = grouped[col].iloc[-1]
        if pd.isna(first_value) or pd.isna(last_value):
            continue
        if first_value == 0:
            percent_change = None
        else:
            percent_change = round(float((last_value - first_value) / abs(first_value) * 100), 2)
        if last_value > first_value:
            direction = "increasing"
        elif last_value < first_value:
            direction = "decreasing"
        else:
            direction = "flat"
        columns[str(col)] = {
            "first_period_average": round(float(first_value), 4),
            "last_period_average": round(float(last_value), 4),
            "percent_change": percent_change,
            "direction": direction,
        }

    if not columns:
        return None

    return {
        "date_column": str(date_col),
        "period": period_label,
        "period_count": int(len(grouped)),
        "date_range": {
            "start": str(parsed_dates[valid].min().date()),
            "end": str(parsed_dates[valid].max().date()),
        },
        "columns": columns,
    }


def _find_group_by_candidates(df, numeric_cols):
    """A column is worth grouping by if it's categorical-shaped: a handful
    of repeated values, not free text and not an ID. Ranked by cardinality
    (fewer distinct groups = a cleaner comparison) and capped."""
    candidates = []
    for col in df.columns:
        if col in numeric_cols or is_id_column(col):
            continue
        non_null = df[col].dropna()
        if len(non_null) == 0:
            continue
        unique_count = non_null.nunique()
        if unique_count < 2 or unique_count > 50:
            continue
        if unique_count / len(non_null) > 0.5:
            continue  # looks like free text or a near-unique identifier
        candidates.append((col, unique_count))
    candidates.sort(key=lambda item: item[1])
    return [col for col, _count in candidates[:MAX_GROUP_COLUMNS_REPORTED]]


def compute_group_comparisons(df):
    """For every categorical-shaped column, compares the average of every
    numeric column across its groups (e.g. "average order value by region"),
    highlighting the highest- and lowest-scoring group for each pair."""
    numeric_cols = [c for c in df.select_dtypes(include="number").columns if not is_id_column(c)]
    if not numeric_cols:
        return []

    group_by_cols = _find_group_by_candidates(df, numeric_cols)
    comparisons = []
    for group_col in group_by_cols:
        for numeric_col in numeric_cols:
            grouped = df.groupby(group_col, observed=True)[numeric_col].mean().dropna().sort_values(ascending=False)
            if len(grouped) < 2:
                continue
            top = grouped.head(MAX_GROUPS_PER_COLUMN)
            comparisons.append({
                "group_by": str(group_col),
                "metric": str(numeric_col),
                "group_averages": {str(k): round(float(v), 4) for k, v in top.items()},
                "highest": {"group": str(grouped.index[0]), "average": round(float(grouped.iloc[0]), 4)},
                "lowest": {"group": str(grouped.index[-1]), "average": round(float(grouped.iloc[-1]), 4)},
            })
    return comparisons


def compute_outliers(df):
    """Classic IQR fences (1.5x the interquartile range beyond Q1/Q3) per
    numeric column. Simple, well-understood, and doesn't assume a normal
    distribution the way a z-score cutoff would."""
    numeric_cols = [c for c in df.select_dtypes(include="number").columns if not is_id_column(c)]
    outliers = {}
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 5:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outlier_values = series[(series < lower_bound) | (series > upper_bound)]
        if len(outlier_values) == 0:
            continue
        outliers[str(col)] = {
            "outlier_count": int(len(outlier_values)),
            "outlier_percent": round(float(len(outlier_values) / len(series) * 100), 2),
            "normal_range": {
                "lower_bound": round(float(lower_bound), 4),
                "upper_bound": round(float(upper_bound), 4),
            },
            "example_values": [round(float(v), 4) for v in outlier_values.head(MAX_OUTLIER_EXAMPLES).tolist()],
        }
    return outliers


def analyze_file(path):
    """Everything profile_file() already reports (per-column stats, blank-like
    and casing issues, duplicate rows/values), plus the analysis a data
    analyst would do next: correlations, trends over time, group-by
    comparisons, and outlier flagging."""
    result = profile_file(path)

    result["correlations"] = []
    result["trends"] = None
    result["group_comparisons"] = []
    result["outliers"] = {}

    if result.get("row_count", 0) == 0:
        return result

    df, _duplicate_column_names, _notes = load_dataframe(path)

    result["correlations"] = compute_correlations(df)
    result["trends"] = compute_trends(df, detect_date_columns(df))
    result["group_comparisons"] = compute_group_comparisons(df)
    result["outliers"] = compute_outliers(df)

    return result


if __name__ == "__main__":
    try:
        file_path = resolve_input_path(sys.argv[1:], os.getcwd(), script_name="analyze.py")
    except ValueError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    try:
        result = analyze_file(file_path)
        if len(sys.argv) == 1:
            result["used_last_gathered_file"] = file_path
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": friendly_error_message(e, file_path)}))
        sys.exit(1)
