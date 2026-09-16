import json
import os
import sys

from gatherer import gather_dataframes
from loaders import load_dataframe


def build_output_folder(first_path):
    """<first file>_gathered_results, next to the first input file (not in the
    current working directory)."""
    first_base = os.path.splitext(first_path)[0]
    folder = f"{first_base}_gathered_results"
    os.makedirs(folder, exist_ok=True)
    return folder

def add_excel_autofilter(worksheet, row_count, column_count):
    from openpyxl.utils import get_column_letter
    if row_count == 0 or column_count == 0:
        return
    last_column_letter = get_column_letter(column_count)
    last_row = row_count + 1
    worksheet.auto_filter.ref = f"A1:{last_column_letter}{last_row}"
    for col_idx, col_name in enumerate(worksheet[1], start=1):
        max_length = max(
            [len(str(col_name.value))] +
            [len(str(cell.value)) for cell in worksheet[get_column_letter(col_idx)][1:200] if cell.value is not None]
        )
        worksheet.column_dimensions[get_column_letter(col_idx)].width = min(max_length + 2, 60)

def gather_files(paths):
    dataframes = []
    filenames = []
    file_notes = {}
    for path in paths:
        df, _dup_cols, notes = load_dataframe(path)
        dataframes.append(df)
        filenames.append(os.path.basename(path))
        if notes:
            file_notes[os.path.basename(path)] = notes

    mode, result, report = gather_dataframes(dataframes, filenames)
    if file_notes:
        report["file_notes"] = file_notes

    output_folder = build_output_folder(paths[0])
    output_path = os.path.join(output_folder, "gathered.xlsx")

    from openpyxl import Workbook
    workbook = Workbook()
    workbook.remove(workbook.active)

    if mode == "joined":
        sheet = workbook.create_sheet("gathered")
        sheet.append(list(result.columns))
        for row in result.itertuples(index=False):
            sheet.append(list(row))
        add_excel_autofilter(sheet, len(result), len(result.columns))
    else:
        for sheet_name, df in result.items():
            sheet = workbook.create_sheet(sheet_name)
            sheet.append(list(df.columns))
            for row in df.itertuples(index=False):
                sheet.append(list(row))
            add_excel_autofilter(sheet, len(df), len(df.columns))

    workbook.save(output_path)

    report["file"] = ", ".join(paths)
    report["output_folder"] = output_folder
    report["gathered_file"] = output_path
    return report

def friendly_error_message(e, paths):
    if isinstance(e, FileNotFoundError):
        return f"Couldn't find one of these files: {', '.join(paths)}. Check the file names and make sure they're all in this folder."
    if isinstance(e, PermissionError):
        return "Couldn't open one of these files - it might be open in another program (like Excel). Close it and try again."
    message = str(e)
    return message

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: python gather.py <file1> <file2> [file3 ...] (at least 2 files needed)"}))
        sys.exit(1)

    file_paths = sys.argv[1:]
    try:
        result = gather_files(file_paths)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": friendly_error_message(e, file_paths)}))
        sys.exit(1)
