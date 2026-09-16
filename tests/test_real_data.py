"""End-to-end tests on real, publicly available datasets in real_data/.

Every expected number here is either a documented property of the dataset
(e.g. Titanic has 891 passengers and 177 missing ages) or is recomputed from the
raw file with plain pandas inside the test, so the assertions do not depend on
the code under test. See real_data/README.md for sources and licences.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
REAL_DATA = REPO_ROOT / "real_data"


@pytest.fixture
def real(tmp_path):
    """Scratch copy of real_data/ so scripts can write *_results folders freely."""
    dest = tmp_path / "real_data"
    shutil.copytree(REAL_DATA, dest, ignore=shutil.ignore_patterns("*_results", "README.md"))
    return dest


def run(python_exe, script, *args, cwd):
    proc = subprocess.run([python_exe, str(script), *args], cwd=cwd, capture_output=True, text=True)
    try:
        return proc.returncode, json.loads(proc.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"script did not print JSON.\nstdout={proc.stdout!r}\nstderr={proc.stderr!r}")


def question_mark_cells(df):
    return df.astype(str).apply(lambda s: s.str.strip() == "?")


# ---------------------------------------------------------------- Titanic (Kaggle / datasciencedojo)


def test_titanic_missing_values_are_filled_with_median_and_unknown(python_exe, scripts_dir, real):
    raw = pd.read_csv(real / "titanic.csv")
    code, r = run(python_exe, scripts_dir / "clean.py", "titanic.csv", cwd=real)
    assert code == 0, r

    assert r["original_row_count"] == 891
    assert r["final_row_count"] == 891  # no exact duplicates in the Titanic data
    assert r["duplicate_rows_removed"] == 0
    assert r["conflicting_duplicate_rows"] == 0  # PassengerId is unique
    assert r["columns_cleaned"]["Age"]["missing_values_filled"] == 177
    assert r["columns_cleaned"]["Cabin"]["missing_values_filled"] == 687
    assert r["columns_cleaned"]["Embarked"]["missing_values_filled"] == 2
    assert r["columns_cleaned"]["Sex"]["categories_standardized"] == 891
    assert r["rows_with_missing_values"] == int(raw.isna().any(axis=1).sum())

    cleaned = pd.read_excel(real / r["cleaned_file"])
    assert not cleaned.isna().any().any()
    assert cleaned.loc[raw["Age"].isna(), "Age"].unique().tolist() == [raw["Age"].median()]
    assert (cleaned.loc[raw["Cabin"].isna(), "Cabin"] == "Unknown").all()
    assert cleaned["Sex"].value_counts().to_dict() == {"Male": 577, "Female": 314}
    # Numeric columns must survive untouched.
    assert cleaned["Fare"].tolist() == raw["Fare"].tolist()
    # Original file is never modified.
    assert (real / "titanic.csv").read_bytes() == (REAL_DATA / "titanic.csv").read_bytes()


# ---------------------------------------------------------------- UCI Adult (census income)


def test_uci_adult_question_marks_and_padding(python_exe, scripts_dir, real):
    raw = pd.read_csv(real / "uci_adult_sample.csv")
    q = question_mark_cells(raw)
    code, r = run(python_exe, scripts_dir / "clean.py", "uci_adult_sample.csv", cwd=real)
    assert code == 0, r

    # Every " ?" cell becomes a real null, then gets filled.
    blank_like = sum(c.get("blank_like_converted_to_null", 0) for c in r["columns_cleaned"].values())
    assert blank_like == int(q.sum().sum()) == 244
    assert r["rows_with_missing_values"] == int(q.any(axis=1).sum()) == 133
    for col in ("workclass", "occupation", "native_country"):
        assert r["columns_cleaned"][col]["missing_values_filled"] == int(q[col].sum())

    # UCI pads every text cell with a leading space; all of them must be trimmed.
    text_cols = [c for c in raw.columns if raw[c].dtype == object]
    for col in text_cols:
        trimmed = r["columns_cleaned"][col]["whitespace_trimmed"]
        assert trimmed == int((raw[col].str.strip() != raw[col]).sum() - q[col].sum())

    # This slice of the data contains exactly one real duplicate row.
    assert r["duplicate_rows_removed"] == int(raw.duplicated().sum()) == 1
    assert r["final_row_count"] == 1499
    assert (real / r["duplicates_file"]).exists()

    cleaned = pd.read_excel(real / r["cleaned_file"])
    assert not cleaned.isna().any().any()
    assert not (cleaned["workclass"] == "?").any()
    assert (cleaned["education"] == cleaned["education"].str.strip()).all()
    assert cleaned["age"].sum() == raw.drop_duplicates()["age"].sum()


# ---------------------------------------------------------------- UCI Automobile (imports-85)


def test_uci_automobile_numeric_columns_recover_from_question_marks(python_exe, scripts_dir, real):
    raw = pd.read_csv(real / "uci_automobile.csv")
    code, r = run(python_exe, scripts_dir / "clean.py", "uci_automobile.csv", cwd=real)
    assert code == 0, r

    # Regression: "width" used to be treated as an ID column ("id" substring)
    # and produced 190 bogus "conflicting duplicate" rows.
    assert r["conflicting_duplicate_rows"] == 0
    assert "conflicts_file" not in r
    assert r["final_row_count"] == 205

    numeric_with_gaps = ["normalized_losses", "bore", "stroke", "horsepower", "peak_rpm", "price"]
    cleaned = pd.read_excel(real / r["cleaned_file"])
    for col in numeric_with_gaps:
        missing = int((raw[col] == "?").sum())
        assert r["columns_cleaned"][col]["blank_like_converted_to_null"] == missing
        assert r["columns_cleaned"][col]["converted_to_numeric"] == 205 - missing
        assert pd.api.types.is_numeric_dtype(cleaned[col]), col
        median = pd.to_numeric(raw[col], errors="coerce").median()
        assert cleaned.loc[raw[col] == "?", col].unique().tolist() == [median], col
    # A text column with "?" gets "Unknown", not a number.
    assert r["columns_cleaned"]["num_of_doors"]["missing_values_filled"] == 2
    assert (cleaned.loc[raw["num_of_doors"] == "?", "num_of_doors"] == "Unknown").all()
    assert not (cleaned.astype(str) == "?").any().any()


# ---------------------------------------------------------------- OpenFlights airlines


def test_openflights_backslash_n_is_a_null_marker(python_exe, scripts_dir, real):
    raw = pd.read_csv(real / "openflights_airlines.csv")
    code, r = run(python_exe, scripts_dir / "clean.py", "openflights_airlines.csv", cwd=real)
    assert code == 0, r

    assert r["original_row_count"] == 1500
    assert r["columns_cleaned"]["alias"]["blank_like_converted_to_null"] == int((raw["alias"] == r"\N").sum()) == 1496
    assert r["columns_cleaned"]["active"]["categories_standardized"] == 1500  # Y/N -> Yes/No
    assert r["conflicting_duplicate_rows"] == 0  # airline_id is unique

    cleaned = pd.read_excel(real / r["cleaned_file"])
    assert set(cleaned["active"].unique()) == {"Yes", "No"}
    assert not (cleaned.astype(str) == r"\N").any().any()
    assert cleaned["airline_id"].tolist() == raw["airline_id"].tolist()


# ---------------------------------------------------------------- Northwind (malformed CSV export)


def test_northwind_customers_malformed_lines_are_skipped_and_reported(python_exe, scripts_dir, real):
    code, r = run(python_exe, scripts_dir / "clean.py", "northwind_customers.csv", cwd=real)
    assert code == 0, r

    # 24 of the 91 customer lines have an unquoted comma in the company name.
    assert r["malformed_rows_skipped"] == 24
    assert r["malformed_row_numbers"][:3] == [8, 9, 10]
    assert r["original_row_count"] == 67
    # SQL "NULL" strings are treated as missing.
    assert r["columns_cleaned"]["region"]["missing_values_filled"] == 45
    assert r["conflicting_duplicate_rows"] == 0


def test_gather_northwind_joins_customers_to_orders(python_exe, scripts_dir, real):
    code, r = run(python_exe, scripts_dir / "gather.py", "northwind_customers.csv", "northwind_orders.csv", cwd=real)
    assert code == 0, r

    assert r["mode"] == "joined"
    assert r["join_column"] == "customerID"
    assert r["join_column_overlap_score"] == 1.0
    assert r["row_counts_per_file"] == {"northwind_customers.csv": 67, "northwind_orders.csv": 654}
    assert r["final_row_count"] == 654  # every order belongs to a loaded customer
    assert r["file_notes"]["northwind_orders.csv"]["malformed_rows_skipped"] == 176
    # Output goes next to the first input file, not into the working directory.
    assert r["output_folder"] == "northwind_customers_gathered_results"
    assert (real / r["gathered_file"]).exists()

    gathered = pd.read_excel(real / r["gathered_file"])
    assert len(gathered) == 654
    assert {"customerID", "companyName", "orderID", "orderDate"} <= set(gathered.columns)
    assert gathered["orderID"].is_unique


def test_gather_unrelated_files_are_kept_as_separate_sheets(python_exe, scripts_dir, real):
    code, r = run(python_exe, scripts_dir / "gather.py", "titanic.csv", "uci_automobile.csv", cwd=real)
    assert code == 0, r
    assert r["mode"] == "linked_sheets"
    sheets = pd.read_excel(real / r["gathered_file"], sheet_name=None)
    assert set(sheets) == {"titanic", "uci_automobile"}
    assert len(sheets["titanic"]) == 891 and len(sheets["uci_automobile"]) == 205


def test_gather_writes_next_to_first_input_when_run_from_elsewhere(python_exe, scripts_dir, real, tmp_path):
    code, r = run(
        python_exe, scripts_dir / "gather.py", str(real / "northwind_customers.csv"), str(real / "northwind_orders.csv"),
        cwd=tmp_path,
    )
    assert code == 0, r
    assert Path(r["gathered_file"]).parent.parent == real
    assert not (tmp_path / "northwind_customers_gathered_results").exists()
