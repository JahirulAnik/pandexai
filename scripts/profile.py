import sys
import json
import pandas as pd


def profile_csv(path):
    df = pd.read_csv(path)
    result = {
        "file": path,
        "row_count": len(df),
        "column_count": len(df.columns),
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

        result["columns"][col] = col_info

    return result


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
