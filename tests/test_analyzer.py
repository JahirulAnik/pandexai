"""Unit tests for scripts/analyze.py's pure analysis functions, using small
synthetic DataFrames so each behavior is isolated. CLI-level black-box
coverage against real public data lives in test_scripts_cli.py.
"""
import pandas as pd
import pytest
from analyze import (
    compute_correlations,
    compute_group_comparisons,
    compute_outliers,
    compute_trends,
    detect_date_columns,
)


def test_detect_date_columns_finds_parseable_date_text():
    df = pd.DataFrame({
        "order_date": ["2024-01-01", "2024-02-15", "2024-03-20", "2024-04-05"],
        "notes": ["a", "b", "c", "d"],
        "amount": [1, 2, 3, 4],
    })
    assert detect_date_columns(df) == ["order_date"]


def test_detect_date_columns_ignores_numeric_and_non_date_text():
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "category": ["red", "green", "blue"],
    })
    assert detect_date_columns(df) == []


def test_detect_date_columns_finds_native_datetime_dtype():
    df = pd.DataFrame({"ts": pd.to_datetime(["2024-01-01", "2024-02-01"])})
    assert detect_date_columns(df) == ["ts"]


def test_compute_correlations_finds_strong_positive_pair():
    df = pd.DataFrame({
        "x": [1, 2, 3, 4, 5, 6, 7, 8],
        "y": [2, 4, 6, 8, 10, 12, 14, 16],  # perfectly correlated with x
        "z": [8, 1, 6, 2, 9, 3, 5, 7],       # unrelated
    })
    pairs = compute_correlations(df)
    assert pairs[0]["column_a"] == "x" and pairs[0]["column_b"] == "y"
    assert pairs[0]["correlation"] == pytest.approx(1.0)
    assert pairs[0]["strength"] == "strong positive"


def test_compute_correlations_excludes_id_columns():
    df = pd.DataFrame({
        "PassengerId": [1, 2, 3, 4, 5],
        "Fare": [10, 20, 15, 25, 30],
    })
    assert compute_correlations(df) == []


def test_compute_correlations_empty_with_fewer_than_two_numeric_columns():
    df = pd.DataFrame({"category": ["a", "b", "c"]})
    assert compute_correlations(df) == []


def test_compute_trends_reports_increasing_direction():
    df = pd.DataFrame({
        "order_date": ["2024-01-01", "2024-01-10", "2024-06-01", "2024-06-15", "2024-12-01", "2024-12-20"],
        "revenue": [100, 110, 200, 210, 400, 410],
    })
    trends = compute_trends(df, ["order_date"])
    assert trends is not None
    assert trends["date_column"] == "order_date"
    assert trends["columns"]["revenue"]["direction"] == "increasing"
    assert trends["columns"]["revenue"]["first_period_average"] < trends["columns"]["revenue"]["last_period_average"]


def test_compute_trends_none_without_date_columns():
    df = pd.DataFrame({"revenue": [100, 200, 300]})
    assert compute_trends(df, []) is None


def test_compute_trends_picks_larger_period_for_wider_date_spans():
    # Multi-year span should bucket by year, not by day.
    dates = [f"{year}-06-15" for year in range(2018, 2024)]
    df = pd.DataFrame({"order_date": dates, "amount": [10, 20, 15, 25, 30, 40]})
    trends = compute_trends(df, ["order_date"])
    assert trends["period"] == "year"


def test_compute_group_comparisons_finds_highest_and_lowest_group():
    df = pd.DataFrame({
        "region": ["East", "East", "West", "West", "North", "North"],
        "sales": [100, 120, 50, 60, 200, 210],
    })
    comparisons = compute_group_comparisons(df)
    match = next(c for c in comparisons if c["group_by"] == "region" and c["metric"] == "sales")
    assert match["highest"]["group"] == "North"
    assert match["lowest"]["group"] == "West"


def test_compute_group_comparisons_skips_high_cardinality_and_id_columns():
    df = pd.DataFrame({
        "customer_id": [f"C{i}" for i in range(20)],  # near-unique, not categorical
        "amount": list(range(20)),
    })
    assert compute_group_comparisons(df) == []


def test_compute_outliers_flags_values_outside_iqr_fences():
    df = pd.DataFrame({"amount": [10, 11, 12, 13, 11, 12, 10, 500]})  # 500 is a clear outlier
    outliers = compute_outliers(df)
    assert "amount" in outliers
    assert outliers["amount"]["outlier_count"] == 1
    assert 500 in outliers["amount"]["example_values"]


def test_compute_outliers_empty_for_uniform_data():
    df = pd.DataFrame({"amount": [10, 10, 10, 10, 10, 10]})
    assert compute_outliers(df) == {}
