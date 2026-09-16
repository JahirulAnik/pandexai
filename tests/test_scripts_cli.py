"""Black-box tests: run the scripts exactly as the AI CLI would, and assert on the
JSON contract that commands/*.md promise."""
import json
import subprocess

import pandas as pd
import pytest


def run(python_exe, script, *args, cwd):
    proc = subprocess.run([python_exe, str(script), *args], cwd=cwd, capture_output=True, text=True)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"script did not print JSON.\nstdout={proc.stdout!r}\nstderr={proc.stderr!r}")
    return proc.returncode, payload


@pytest.mark.parametrize(
    "name",
    ["clean_data.csv", "messy_data.csv", "large_data.csv", "all_null_column.csv", "one_column.csv", "mixed_encoding.csv"],
)
def test_clean_succeeds_on_valid_fixtures(python_exe, scripts_dir, fixtures, name):
    code, report = run(python_exe, scripts_dir / "clean.py", name, cwd=fixtures)
    assert code == 0, report
    for key in ("original_row_count", "final_row_count", "output_folder", "cleaned_file", "columns_cleaned"):
        assert key in report
    out = fixtures / report["cleaned_file"]
    assert out.suffix == ".xlsx" and out.exists()
    df = pd.read_excel(out)
    assert len(df) == report["final_row_count"]
    assert not df.isna().any().any(), "cleaned.xlsx must have no missing values"
    # Original file must be untouched.
    from conftest import FIXTURES_DIR

    assert (fixtures / name).read_bytes() == (FIXTURES_DIR / name).read_bytes()


def test_clean_reports_review_files_and_counts(python_exe, scripts_dir, fixtures):
    code, r = run(python_exe, scripts_dir / "clean.py", "test_all_cases_v2.csv", cwd=fixtures)
    assert code == 0
    assert r["original_row_count"] == 6
    assert r["empty_rows_removed"] == 1
    assert r["conflicting_duplicate_rows"] == 2
    assert r["rows_with_missing_values"] == 3
    assert r["final_row_count"] == 5
    for key in ("conflicts_file", "missing_values_file", "empty_rows_file"):
        path = fixtures / r[key]
        assert path.exists()
        assert "reason" in pd.read_excel(path).columns


def test_clean_cleaned_xlsx_has_autofilter(python_exe, scripts_dir, fixtures):
    from openpyxl import load_workbook

    _, r = run(python_exe, scripts_dir / "clean.py", "clean_data.csv", cwd=fixtures)
    ws = load_workbook(fixtures / r["cleaned_file"]).active
    assert ws.auto_filter.ref == "A1:D5"


def test_clean_latin1_fallback_reports_encoding_note(python_exe, scripts_dir, fixtures):
    _, r = run(python_exe, scripts_dir / "clean.py", "mixed_encoding.csv", cwd=fixtures)
    assert "encoding_note" in r
    assert pd.read_excel(fixtures / r["cleaned_file"])["city"].tolist() == ["Zürich", "Café", "São Paulo"]


@pytest.mark.parametrize(
    "name, fragment",
    [
        ("empty_file.csv", "no columns or rows"),
        ("corrupted.xlsx", "valid Excel file"),
        ("does_not_exist.csv", "Couldn't find a file"),
    ],
)
def test_clean_friendly_errors(python_exe, scripts_dir, fixtures, name, fragment):
    code, r = run(python_exe, scripts_dir / "clean.py", name, cwd=fixtures)
    assert code == 1
    assert fragment in r["error"]


def test_clean_usage_error(python_exe, scripts_dir, fixtures):
    code, r = run(python_exe, scripts_dir / "clean.py", cwd=fixtures)
    assert code == 1 and "Usage" in r["error"]


def test_gather_joined_mode(python_exe, scripts_dir, tmp_path):
    pd.DataFrame({"order_id": [1, 2, 3], "amount": [1, 2, 3]}).to_csv(tmp_path / "sales.csv", index=False)
    pd.DataFrame({"order_id": [1, 2, 3], "carrier": list("abc")}).to_csv(tmp_path / "cost.csv", index=False)
    code, r = run(python_exe, scripts_dir / "gather.py", "sales.csv", "cost.csv", cwd=tmp_path)
    assert code == 0
    assert r["mode"] == "joined" and r["join_column"] == "order_id"
    assert r["final_row_count"] == 3
    sheets = pd.read_excel(tmp_path / r["gathered_file"], sheet_name=None)
    assert list(sheets) == ["gathered"]


def test_gather_linked_sheets_mode(python_exe, scripts_dir, fixtures):
    code, r = run(python_exe, scripts_dir / "gather.py", "clean_data.csv", "one_column.csv", cwd=fixtures)
    assert code == 0 and r["mode"] == "linked_sheets"
    sheets = pd.read_excel(fixtures / r["gathered_file"], sheet_name=None)
    assert set(sheets) == {"clean_data", "one_column"}


def test_gather_requires_two_files(python_exe, scripts_dir, fixtures):
    code, r = run(python_exe, scripts_dir / "gather.py", "clean_data.csv", cwd=fixtures)
    assert code == 1 and "at least 2 files" in r["error"]


def test_profile_reports_quality_signals(python_exe, scripts_dir, fixtures):
    code, r = run(python_exe, scripts_dir / "profile.py", "messy_data.csv", cwd=fixtures)
    assert code == 0
    assert r["row_count"] == 6 and r["column_count"] == 5
    assert "inconsistent_casing_example" in r["columns"]["region"]
    assert r["columns"]["customer_id"]["duplicate_values"]["examples"] == {"2": 2}
    # "N/A" and "null" are parsed as real NaN by pandas; only "-" survives as text.
    assert r["columns"]["signup_date"]["blank_like_count"] == 1
