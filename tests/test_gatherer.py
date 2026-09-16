"""Unit tests for scripts/gatherer.py join-column detection and merging."""
import pandas as pd
from gatherer import find_shared_columns, gather_dataframes, overlap_score, pick_join_column


def test_find_shared_columns_is_case_insensitive():
    a = pd.DataFrame({"Order_ID": [1], "x": [1]})
    b = pd.DataFrame({"order_id": [1], "y": [1]})
    assert find_shared_columns([a, b]) == ["Order_ID"]


def test_overlap_score_rewards_real_value_overlap():
    a = pd.DataFrame({"k": [1, 2, 3]})
    b = pd.DataFrame({"k": [2, 3, 4]})
    assert abs(overlap_score([a, b], "k") - (2 / 3)) < 1e-9


def test_pick_join_column_rejects_coincidental_name_match():
    a = pd.DataFrame({"notes": ["foo", "bar"], "id": [1, 2]})
    b = pd.DataFrame({"notes": ["baz", "qux"], "id": [9, 8]})
    col, score = pick_join_column([a, b])
    assert col is None
    assert score < 0.3


def test_gather_joins_on_strong_column_with_outer_join():
    sales = pd.DataFrame({"order_id": [1, 2, 3], "amount": [10, 20, 30]})
    cost = pd.DataFrame({"order_id": [2, 3, 4], "ship": [1, 2, 3]})
    mode, result, report = gather_dataframes([sales, cost], ["sales.csv", "cost.csv"])
    assert mode == "joined"
    assert report["join_column"] == "order_id"
    assert report["final_row_count"] == 4  # outer join keeps every order
    assert list(result.columns) == ["order_id", "amount", "ship"]


def test_gather_falls_back_to_linked_sheets():
    a = pd.DataFrame({"a": [1]})
    b = pd.DataFrame({"b": [2]})
    mode, result, report = gather_dataframes([a, b], ["first.csv", "second.csv"])
    assert mode == "linked_sheets"
    assert set(result.keys()) == {"first", "second"}
    assert "reason" in report
