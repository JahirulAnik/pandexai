"""Unit tests for scripts/gather.py's file-discovery and chaining helpers
(the logic behind running "/pandex gather" or "/pandex clean" with no
filenames). CLI-level black-box coverage of the same behavior lives in
test_scripts_cli.py; these are faster, more targeted checks of the pure
functions.
"""
import json

import pytest
from clean import read_last_gathered_state, resolve_input_path
from gather import discover_data_files, resolve_input_paths, write_last_gathered_state


def test_discover_data_files_finds_supported_extensions(tmp_path):
    (tmp_path / "a.csv").write_text("x")
    (tmp_path / "b.XLSX").write_text("x")  # extension matching is case-insensitive
    (tmp_path / "c.json").write_text("x")
    (tmp_path / "d.txt").write_text("x")  # not a supported data extension
    assert discover_data_files(tmp_path) == ["a.csv", "b.XLSX", "c.json"]


def test_discover_data_files_ignores_hidden_and_subfolders(tmp_path):
    (tmp_path / "visible.csv").write_text("x")
    (tmp_path / ".hidden.csv").write_text("x")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "nested.csv").write_text("x")  # not discovered, discovery is top-level only
    assert discover_data_files(tmp_path) == ["visible.csv"]


def test_resolve_input_paths_passes_through_explicit_filenames(tmp_path):
    assert resolve_input_paths(["a.csv", "b.csv"], tmp_path) == ["a.csv", "b.csv"]


def test_resolve_input_paths_rejects_single_filename(tmp_path):
    with pytest.raises(ValueError, match="at least 2 files"):
        resolve_input_paths(["a.csv"], tmp_path)


def test_resolve_input_paths_autodiscovers_when_none_given(tmp_path):
    (tmp_path / "a.csv").write_text("x")
    (tmp_path / "b.csv").write_text("x")
    assert resolve_input_paths([], tmp_path) == ["a.csv", "b.csv"]


def test_resolve_input_paths_errors_with_count_when_too_few_discovered(tmp_path):
    (tmp_path / "a.csv").write_text("x")
    with pytest.raises(ValueError, match="found 1"):
        resolve_input_paths([], tmp_path)


def test_write_and_read_last_gathered_state_round_trip(tmp_path):
    write_last_gathered_state("sales_gathered_results/gathered.xlsx", tmp_path)
    state_file = tmp_path / ".pandex" / "state.json"
    assert json.loads(state_file.read_text()) == {"last_gathered": "sales_gathered_results/gathered.xlsx"}
    assert read_last_gathered_state(tmp_path) == "sales_gathered_results/gathered.xlsx"


def test_write_last_gathered_state_is_a_noop_without_a_path(tmp_path):
    write_last_gathered_state(None, tmp_path)
    assert not (tmp_path / ".pandex").exists()


def test_read_last_gathered_state_returns_none_when_absent(tmp_path):
    assert read_last_gathered_state(tmp_path) is None


def test_resolve_input_path_single_filename_passes_through(tmp_path):
    assert resolve_input_path(["a.csv"], tmp_path) == "a.csv"


def test_resolve_input_path_too_many_args_is_usage_error(tmp_path):
    with pytest.raises(ValueError, match="Usage"):
        resolve_input_path(["a.csv", "b.csv"], tmp_path)


def test_resolve_input_path_falls_back_to_last_gathered(tmp_path):
    gathered_dir = tmp_path / "sales_gathered_results"
    gathered_dir.mkdir()
    gathered_file = gathered_dir / "gathered.xlsx"
    gathered_file.write_text("x")
    write_last_gathered_state("sales_gathered_results/gathered.xlsx", tmp_path)

    resolved = resolve_input_path([], tmp_path)
    assert resolved == str(gathered_file)


def test_resolve_input_path_no_filename_and_no_state_errors(tmp_path):
    with pytest.raises(ValueError, match="No filename was given"):
        resolve_input_path([], tmp_path)


def test_resolve_input_path_last_gathered_file_missing_errors(tmp_path):
    write_last_gathered_state("does_not_exist_results/gathered.xlsx", tmp_path)
    with pytest.raises(ValueError, match="no longer exists"):
        resolve_input_path([], tmp_path)
