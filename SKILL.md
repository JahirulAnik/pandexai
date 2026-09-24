# PandexAI

PandexAI is an AI-native data cleaning CLI. It runs inside AI coding CLIs
(Claude Code, Cursor, etc.) to handle deterministic data work as real code,
and hands the AI clean, structured output to reason over.

## Core rule: judgment vs execution

- Execution (deterministic): anything that computes numbers from data MUST
  run as real Python/pandas code in scripts/. Never let the AI estimate or
  guess statistics, column types, null counts, or any other figure that a
  script can compute exactly.
- Judgment (AI): interpreting results, flagging likely issues, suggesting
  next steps, and writing human-readable summaries is the AI's job.

This split exists so PandexAI's numbers are always trustworthy: they come
from real computation, not a language model's guess.

## Running scripts

Always use the project's own interpreter, never the system Python:

- Mac/Linux: `.pandex/venv/bin/python scripts/<script>.py ...`
- Windows: `.pandex\venv\Scripts\python.exe scripts\<script>.py ...`

Every script prints exactly one JSON object. Exit code 0 means success;
exit code 1 means the JSON contains an "error" field with a plain-English
message to relay to the user. A successful report may also carry notes
about the input that the user must hear: "encoding_note" (file was not
UTF-8) and "malformed_rows_skipped" with "malformed_row_numbers" (CSV lines
with the wrong number of fields were left out). Always relay those.

## Available commands

- clean - diagnoses and cleans a CSV, Excel or JSON file, writing
  cleaned.xlsx and review files into <name>_cleaned_results/. See
  commands/clean.md.
- gather - combines two or more files into one workbook, joining on a
  column with real value overlap or keeping them as linked sheets. See
  commands/gather.md.
- profile - read-only per-column statistics and data-quality signals for a
  single file (nulls, blanks, casing, duplicates). Nothing is written to
  disk. See commands/profile.md.
- analyze - the full read-only analysis: everything profile reports, plus
  correlations, trends over time, group comparisons, and outlier flagging.
  Nothing is written to disk. See commands/analyze.md.
