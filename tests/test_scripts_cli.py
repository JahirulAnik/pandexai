"""Black-box tests of the JSON / exit-code contract that commands/*.md promise.

Dataset-level behaviour is tested on real public data in test_real_data.py. The
files in test_fixtures/ only cover failure paths that cannot be downloaded:
an empty file, a corrupted .xlsx, a latin-1 encoded export, and one hand-made
CSV (test_all_cases_v2.csv) that has a conflicting-ID row and a fully empty row
in the same file, which the public datasets do not.
"""
import json
import subprocess

import pandas as pd
import pytest
from conftest import REAL_DATA_DIR


def run(python_exe, script, *args, cwd):
    proc = subprocess.run([python_exe, str(script), *args], cwd=cwd, capture_output=True, text=True)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"script did not print JSON.\nstdout={proc.stdout!r}\nstderr={proc.stderr!r}")
    return proc.returncode, payload


def test_clean_report_contract_on_real_file(python_exe, scripts_dir, tmp_path):
    src = REAL_DATA_DIR / "titanic.csv"
    (tmp_path / "titanic.csv").write_bytes(src.read_bytes())
    code, report = run(python_exe, scripts_dir / "clean.py", "titanic.csv", cwd=tmp_path)
    assert code == 0, report
    for key in ("original_row_count", "final_row_count", "output_folder", "cleaned_file", "columns_cleaned",
                "duplicate_rows_removed", "conflicting_duplicate_rows", "rows_with_missing_values", "empty_rows_removed"):
        assert key in report
    out = tmp_path / report["cleaned_file"]
    assert out.suffix == ".xlsx" and out.exists()
    assert report["output_folder"] == "titanic_cleaned_results"
    # cleaned.xlsx has an AutoFilter spanning every column and row.
    from openpyxl import load_workbook

    ws = load_workbook(out).active
    assert ws.auto_filter.ref == f"A1:L{report['final_row_count'] + 1}"
    # Original file is untouched.
    assert (tmp_path / "titanic.csv").read_bytes() == src.read_bytes()


def test_clean_reports_conflicts_and_empty_rows(python_exe, scripts_dir, fixtures):
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


def test_gather_requires_two_files(python_exe, scripts_dir, fixtures):
    code, r = run(python_exe, scripts_dir / "gather.py", "mixed_encoding.csv", cwd=fixtures)
    assert code == 1 and "at least 2 files" in r["error"]


def test_profile_reports_real_column_statistics(python_exe, scripts_dir, tmp_path):
    src = REAL_DATA_DIR / "titanic.csv"
    (tmp_path / "titanic.csv").write_bytes(src.read_bytes())
    code, r = run(python_exe, scripts_dir / "profile.py", "titanic.csv", cwd=tmp_path)
    assert code == 0
    raw = pd.read_csv(src)
    assert r["row_count"] == 891 and r["column_count"] == 12
    assert r["columns"]["Age"]["null_count"] == 177
    assert r["columns"]["Age"]["median"] == raw["Age"].median()
    assert r["columns"]["Fare"]["max"] == raw["Fare"].max()
    assert r["columns"]["Sex"]["unique_count"] == 2
