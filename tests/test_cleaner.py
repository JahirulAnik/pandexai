"""Unit tests for the pure-pandas transforms in scripts/cleaner.py."""
import numpy as np
import pandas as pd
from cleaner import (
    clean_dataframe,
    coerce_numeric,
    fill_missing,
    is_id_column,
    normalize_blank_like,
    standardize_casing,
    standardize_dates,
    standardize_known_categories,
    trim_whitespace,
)


def test_trim_whitespace_counts_only_real_changes():
    s = pd.Series([" a", "b", np.nan, "c "])
    out, changed = trim_whitespace(s)
    assert out.tolist()[:2] == ["a", "b"]
    assert pd.isna(out.iloc[2])
    # Regression: NaN cells must not be counted as "trimmed" (NaN != NaN is True).
    assert changed == 2


def test_normalize_blank_like():
    s = pd.Series(["x", "N/A", "", "-", "null", " none ", "ok"])
    out, changed = normalize_blank_like(s)
    assert changed == 5
    assert out.isna().sum() == 5
    assert out.iloc[0] == "x" and out.iloc[6] == "ok"


def test_standardize_casing_picks_most_common_variant():
    s = pd.Series(["North", "north", "North", "NORTH", "South"])
    out, changed = standardize_casing(s)
    assert out.tolist() == ["North"] * 4 + ["South"]
    assert changed == 2


def test_standardize_known_categories_gender():
    s = pd.Series(["M", "male", "f", "Female", np.nan])
    out, changed = standardize_known_categories(s)
    assert out.tolist()[:4] == ["Male", "Male", "Female", "Female"]
    assert changed == 3


def test_standardize_known_categories_leaves_unrelated_alone():
    s = pd.Series(["apple", "banana"])
    out, changed = standardize_known_categories(s)
    assert changed == 0
    assert out.tolist() == ["apple", "banana"]


def test_standardize_dates_mixed_formats():
    s = pd.Series(["2024-01-05", "01/06/2024", "Jan 8 2024", np.nan])
    out, changed = standardize_dates(s, "signup_date")
    assert out.tolist()[:3] == ["2024-01-05", "2024-01-06", "2024-01-08"]
    assert changed == 2


def test_standardize_dates_skips_id_columns():
    s = pd.Series(["2024-01-05", "01/06/2024"])
    _, changed = standardize_dates(s, "order_id")
    assert changed == 0


def test_fill_missing_numeric_uses_median_text_uses_unknown():
    num, n = fill_missing(pd.Series([1.0, np.nan, 3.0]))
    assert n == 1 and num.tolist() == [1.0, 2.0, 3.0]
    txt, t = fill_missing(pd.Series(["a", None]))
    assert t == 1 and txt.tolist() == ["a", "Unknown"]


def test_clean_dataframe_end_to_end():
    df = pd.DataFrame(
        {
            "customer_id": [1, 2, 2, 3, 4, 4],
            "region": ["North", "south", "South", "South", None, None],
            "amount": [100.0, 200.0, 200.0, None, None, None],
            "gender": ["M", "Male", "Female", "f", None, None],
        }
    )
    cleaned, report, dups, missing, empty, conflicts = clean_dataframe(df)

    assert report["original_row_count"] == 6
    # Rows 5 and 6 are blank apart from the ID -> removed as empty.
    assert report["empty_rows_removed"] == 2
    assert len(empty) == 2
    # customer_id 2 appears twice with differing gender -> conflict, not duplicate.
    assert report["conflicting_duplicate_rows"] == 2
    assert "gender" in conflicts["reason"].iloc[0]
    assert report["duplicate_rows_removed"] == 0
    # Row 4 has a missing amount.
    assert report["rows_with_missing_values"] == 1
    assert report["final_row_count"] == 4
    # No NaN survives in the cleaned output.
    assert not cleaned.isna().any().any()
    assert set(cleaned["region"]) == {"North", "South"}
    assert set(cleaned["gender"]) == {"Male", "Female"}


def test_clean_dataframe_removes_exact_duplicates():
    df = pd.DataFrame({"id": [1, 1], "v": ["x", "x "]})
    cleaned, report, dups, *_ = clean_dataframe(df)
    assert report["duplicate_rows_removed"] == 1
    assert len(dups) == 2  # both members of the group are reported for review
    assert len(cleaned) == 1


def test_is_id_column_matches_whole_words_only():
    for name in ("id", "ID", "order_id", "Order ID", "customerID", "PassengerId", "airline_id", "id_number"):
        assert is_id_column(name), name
    # Regression: these contain "id" as a substring and used to be treated as IDs.
    for name in ("width", "valid", "paid", "holiday", "residence", "symboling"):
        assert not is_id_column(name), name


def test_coerce_numeric_recovers_columns_broken_by_missing_markers():
    s = pd.Series(["12", " 7.5", np.nan, "3"])
    out, changed = coerce_numeric(s)
    assert changed == 3
    assert pd.api.types.is_numeric_dtype(out)
    assert out.tolist()[:2] == [12.0, 7.5]

    # Leading zeros mean codes (postal codes, "007"), not numbers: leave as text.
    codes, changed = coerce_numeric(pd.Series(["05021", "12209", np.nan]))
    assert changed == 0 and not pd.api.types.is_numeric_dtype(codes)
    # Mixed text stays text.
    mixed, changed = coerce_numeric(pd.Series(["12", "twelve"]))
    assert changed == 0


def test_normalize_blank_like_knows_real_world_markers():
    s = pd.Series(["?", " ? ", "\\N", "NULL", "#N/A", "--", "ok"])
    out, changed = normalize_blank_like(s)
    assert changed == 6 and out.iloc[6] == "ok"
