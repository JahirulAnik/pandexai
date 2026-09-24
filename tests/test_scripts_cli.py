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


def test_clean_too_many_args_is_usage_error(python_exe, scripts_dir, fixtures):
    code, r = run(python_exe, scripts_dir / "clean.py", "a.csv", "b.csv", cwd=fixtures)
    assert code == 1 and "Usage" in r["error"]


def test_clean_no_filename_without_gathered_state_errors(python_exe, scripts_dir, fixtures):
    code, r = run(python_exe, scripts_dir / "clean.py", cwd=fixtures)
    assert code == 1
    assert "No filename was given" in r["error"]
    assert "gather" in r["error"]


def test_clean_no_filename_uses_last_gathered_file(python_exe, scripts_dir, tmp_path):
    # Northwind customers/orders share a real, high-cardinality customerID
    # join key - a sane real-world gather, unlike joining a file with itself.
    (tmp_path / "northwind_customers.csv").write_bytes((REAL_DATA_DIR / "northwind_customers.csv").read_bytes())
    (tmp_path / "northwind_orders.csv").write_bytes((REAL_DATA_DIR / "northwind_orders.csv").read_bytes())

    gather_code, gather_report = run(
        python_exe, scripts_dir / "gather.py", "northwind_customers.csv", "northwind_orders.csv", cwd=tmp_path
    )
    assert gather_code == 0, gather_report
    assert (tmp_path / ".pandex" / "state.json").exists()

    clean_code, clean_report = run(python_exe, scripts_dir / "clean.py", cwd=tmp_path)
    assert clean_code == 0, clean_report
    # resolve_input_path returns an absolute path (it has to, to open the file
    # regardless of cwd); the state file itself stores the relative path.
    expected = str(tmp_path / gather_report["gathered_file"])
    assert clean_report["used_last_gathered_file"] == expected
    assert clean_report["file"] == expected


def test_clean_no_filename_reports_missing_gathered_file(python_exe, scripts_dir, tmp_path):
    pandex_dir = tmp_path / ".pandex"
    pandex_dir.mkdir()
    (pandex_dir / "state.json").write_text('{"last_gathered": "does_not_exist_gathered_results/gathered.xlsx"}')

    code, r = run(python_exe, scripts_dir / "clean.py", cwd=tmp_path)
    assert code == 1
    assert "no longer exists" in r["error"]


def test_gather_requires_two_files(python_exe, scripts_dir, fixtures):
    code, r = run(python_exe, scripts_dir / "gather.py", "mixed_encoding.csv", cwd=fixtures)
    assert code == 1 and "at least 2 files" in r["error"]


def test_gather_no_filenames_autodiscovers_project_files(python_exe, scripts_dir, tmp_path):
    (tmp_path / "northwind_customers.csv").write_bytes((REAL_DATA_DIR / "northwind_customers.csv").read_bytes())
    (tmp_path / "northwind_orders.csv").write_bytes((REAL_DATA_DIR / "northwind_orders.csv").read_bytes())
    # A hidden file and a non-data file should be ignored by discovery.
    (tmp_path / ".hidden.csv").write_text("a,b\n1,2\n")
    (tmp_path / "notes.txt").write_text("not a data file")

    code, r = run(python_exe, scripts_dir / "gather.py", cwd=tmp_path)
    assert code == 0, r
    assert sorted(r["auto_discovered_files"]) == ["northwind_customers.csv", "northwind_orders.csv"]
    assert r["mode"] == "joined"


def test_gather_no_filenames_needs_at_least_two_discovered(python_exe, scripts_dir, tmp_path):
    (tmp_path / "only_one.csv").write_text("a,b\n1,2\n")
    code, r = run(python_exe, scripts_dir / "gather.py", cwd=tmp_path)
    assert code == 1
    assert "found 1" in r["error"]


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


def test_analyze_includes_every_profile_field_plus_its_own(python_exe, scripts_dir, tmp_path):
    src = REAL_DATA_DIR / "titanic.csv"
    (tmp_path / "titanic.csv").write_bytes(src.read_bytes())
    profile_code, profile_report = run(python_exe, scripts_dir / "profile.py", "titanic.csv", cwd=tmp_path)
    analyze_code, analyze_report = run(python_exe, scripts_dir / "analyze.py", "titanic.csv", cwd=tmp_path)
    assert profile_code == 0 and analyze_code == 0
    for key in profile_report:
        assert analyze_report[key] == profile_report[key]
    for key in ("correlations", "trends", "group_comparisons", "outliers"):
        assert key in analyze_report
    # Original file is untouched - analyze is read-only, no results folder.
    assert (tmp_path / "titanic.csv").read_bytes() == src.read_bytes()
    assert not (tmp_path / "titanic_analyzed_results").exists()


def test_analyze_correlations_on_real_data(python_exe, scripts_dir, tmp_path):
    src = REAL_DATA_DIR / "uci_automobile.csv"
    (tmp_path / "uci_automobile.csv").write_bytes(src.read_bytes())
    code, r = run(python_exe, scripts_dir / "analyze.py", "uci_automobile.csv", cwd=tmp_path)
    assert code == 0, r
    top = r["correlations"][0]
    # city_mpg and highway_mpg are, correctly, almost perfectly correlated in this dataset.
    assert {top["column_a"], top["column_b"]} == {"city_mpg", "highway_mpg"}
    assert top["correlation"] > 0.9
    assert top["strength"] == "strong positive"
    # Sorted strongest-first, and capped rather than dumping every pair on a
    # dataset with this many numeric columns.
    magnitudes = [abs(pair["correlation"]) for pair in r["correlations"]]
    assert magnitudes == sorted(magnitudes, reverse=True)
    assert len(r["correlations"]) <= 15


def test_analyze_trends_on_real_dated_data(python_exe, scripts_dir, tmp_path):
    src = REAL_DATA_DIR / "northwind_orders.csv"
    (tmp_path / "northwind_orders.csv").write_bytes(src.read_bytes())
    code, r = run(python_exe, scripts_dir / "analyze.py", "northwind_orders.csv", cwd=tmp_path)
    assert code == 0, r
    assert r["trends"] is not None
    assert r["trends"]["date_column"] == "orderDate"
    assert r["trends"]["period"] in ("month", "year")
    assert "freight" in r["trends"]["columns"]
    assert r["trends"]["columns"]["freight"]["direction"] in ("increasing", "decreasing", "flat")
    # freight has real outliers in this dataset (large one-off shipments).
    assert "freight" in r["outliers"]
    assert r["outliers"]["freight"]["outlier_count"] > 0
    # shipRegion/shipCountry are real categorical columns worth comparing by.
    group_by_columns = {c["group_by"] for c in r["group_comparisons"]}
    assert "shipCountry" in group_by_columns


def test_analyze_trends_is_null_without_a_date_column(python_exe, scripts_dir, tmp_path):
    src = REAL_DATA_DIR / "titanic.csv"
    (tmp_path / "titanic.csv").write_bytes(src.read_bytes())
    code, r = run(python_exe, scripts_dir / "analyze.py", "titanic.csv", cwd=tmp_path)
    assert code == 0, r
    assert r["trends"] is None


def test_analyze_too_many_args_is_usage_error(python_exe, scripts_dir, fixtures):
    code, r = run(python_exe, scripts_dir / "analyze.py", "a.csv", "b.csv", cwd=fixtures)
    assert code == 1
    assert "Usage: python analyze.py" in r["error"]


def test_analyze_no_filename_without_gathered_state_errors(python_exe, scripts_dir, fixtures):
    code, r = run(python_exe, scripts_dir / "analyze.py", cwd=fixtures)
    assert code == 1
    assert "No filename was given" in r["error"]
    assert "gather" in r["error"]


def test_analyze_no_filename_uses_last_gathered_file(python_exe, scripts_dir, tmp_path):
    (tmp_path / "northwind_customers.csv").write_bytes((REAL_DATA_DIR / "northwind_customers.csv").read_bytes())
    (tmp_path / "northwind_orders.csv").write_bytes((REAL_DATA_DIR / "northwind_orders.csv").read_bytes())

    gather_code, gather_report = run(
        python_exe, scripts_dir / "gather.py", "northwind_customers.csv", "northwind_orders.csv", cwd=tmp_path
    )
    assert gather_code == 0, gather_report

    analyze_code, analyze_report = run(python_exe, scripts_dir / "analyze.py", cwd=tmp_path)
    assert analyze_code == 0, analyze_report
    expected = str(tmp_path / gather_report["gathered_file"])
    assert analyze_report["used_last_gathered_file"] == expected
    assert analyze_report["file"] == expected


def test_analyze_friendly_errors(python_exe, scripts_dir, fixtures):
    code, r = run(python_exe, scripts_dir / "analyze.py", "does_not_exist.csv", cwd=fixtures)
    assert code == 1
    assert "Couldn't find a file" in r["error"]


def test_analyze_warns_on_zero_row_file_instead_of_crashing(python_exe, scripts_dir, tmp_path):
    (tmp_path / "headers_only.csv").write_text("a,b,c\n")
    code, r = run(python_exe, scripts_dir / "analyze.py", "headers_only.csv", cwd=tmp_path)
    assert code == 0
    assert "warning" in r
    assert r["correlations"] == [] and r["trends"] is None and r["group_comparisons"] == [] and r["outliers"] == {}
