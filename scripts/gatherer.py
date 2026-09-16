
def normalize_col_name(name):
    return str(name).strip().lower()

def find_shared_columns(dataframes):
    """Returns a list of column names (original casing from the first
    dataframe) that appear (case-insensitively) in every dataframe."""
    if not dataframes:
        return []
    name_sets = []
    for df in dataframes:
        name_sets.append(set(normalize_col_name(c) for c in df.columns))
    common = set.intersection(*name_sets)
    if not common:
        return []
    first_df_columns = {normalize_col_name(c): c for c in dataframes[0].columns}
    return [first_df_columns[c] for c in common]

def overlap_score(dataframes, col_name):
    """How well a candidate join column's actual VALUES overlap across all
    files - not just the column name. Returns a 0-1 score: the average
    fraction of each file's non-null values that also appear in every other
    file. A column name matching by coincidence (e.g. both files have a
    'notes' column) will score near 0 here."""
    value_sets = []
    for df in dataframes:
        matching = [c for c in df.columns if normalize_col_name(c) == normalize_col_name(col_name)]
        if not matching:
            return 0.0
        col = df[matching[0]]
        values = set(col.dropna().astype(str).str.strip().str.lower().unique())
        if not values:
            return 0.0
        value_sets.append(values)

    scores = []
    for i, values in enumerate(value_sets):
        others = set.union(*(value_sets[:i] + value_sets[i + 1:]))
        if not others:
            scores.append(0.0)
            continue
        overlap = len(values & others) / len(values)
        scores.append(overlap)
    return sum(scores) / len(scores)

def pick_join_column(dataframes, min_overlap=0.3):
    """Finds the best shared column to join on, requiring real value overlap
    (not just a matching column name) above min_overlap. Returns
    (column_name, score) or (None, 0) if nothing qualifies."""
    candidates = find_shared_columns(dataframes)
    if not candidates:
        return None, 0.0

    best_col = None
    best_score = 0.0
    for col in candidates:
        score = overlap_score(dataframes, col)
        if score > best_score:
            best_score = score
            best_col = col

    if best_score >= min_overlap:
        return best_col, best_score
    return None, best_score

def gather_dataframes(dataframes, filenames):
    """Combines a list of dataframes. Returns (mode, result, report):
    mode is "joined" or "linked_sheets".
    - "joined": result is a single merged dataframe (outer join on the
      detected shared column, so no rows from any file are dropped).
    - "linked_sheets": result is a dict of {sheet_name: dataframe}, used
      when no reliable shared column was found - each file's data is kept
      intact rather than forcing a bad join.
    """
    report = {
        "files_gathered": filenames,
        "row_counts_per_file": {name: len(df) for name, df in zip(filenames, dataframes)},
    }

    join_col, score = pick_join_column(dataframes)

    if join_col is None:
        report["mode"] = "linked_sheets"
        report["reason"] = "No column with strong matching values was found across all files, so they were kept as separate sheets instead of forcing an incorrect join."
        sheets = {}
        for name, df in zip(filenames, dataframes):
            sheet_name = name.rsplit(".", 1)[0][:31]
            sheets[sheet_name] = df
        return "linked_sheets", sheets, report

    report["mode"] = "joined"
    report["join_column"] = join_col
    report["join_column_overlap_score"] = round(score, 3)

    result = dataframes[0]
    for i in range(1, len(dataframes)):
        right = dataframes[i]
        right_join_col = next(c for c in right.columns if normalize_col_name(c) == normalize_col_name(join_col))
        left_join_col = next(c for c in result.columns if normalize_col_name(c) == normalize_col_name(join_col))
        result = result.merge(
            right,
            left_on=left_join_col,
            right_on=right_join_col,
            how="outer",
            suffixes=("", f"_{filenames[i].rsplit('.', 1)[0]}")
        )
        if left_join_col != right_join_col and right_join_col in result.columns:
            result = result.drop(columns=[right_join_col])

    report["final_row_count"] = len(result)
    return "joined", result, report
