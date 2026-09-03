---
description: Run PandexAI commands (clean, gather, analyze) for deterministic data profiling and cleaning
---

# Pandex

You are handling a `/pandex` command. The arguments passed are: $ARGUMENTS

Parse the first word as the subcommand, and everything after it as the filename(s) (if any).

## If subcommand is "clean"

1. Read SKILL.md and commands/clean.md in this project for full instructions.
2. If no filename was given, tell the user a filename is required for now (`/pandex gather` is for combining multiple files instead).
3. Run: python scripts/clean.py <filename>
   Use the project's virtual environment Python, not the system one:
   - Windows: .pandex\venv\Scripts\python.exe
   - Mac/Linux: .pandex/venv/bin/python
4. The script prints a JSON report. Do NOT recompute, estimate, or guess any of these numbers yourself.
5. Present the report to the user as a clear, readable summary: what was changed, and list every file created inside the results folder. Make clear their original file was never modified.

## If subcommand is "gather"

1. Read SKILL.md and commands/gather.md in this project for full instructions.
2. Requires at least 2 filenames. If fewer than 2 were given, tell the user they need to list at least two files, e.g. `/pandex gather sales.xlsx cost.xlsx`.
3. Run: python scripts/gather.py <file1> <file2> [file3 ...]
   Use the project's virtual environment Python, not the system one:
   - Windows: .pandex\venv\Scripts\python.exe
   - Mac/Linux: .pandex/venv/bin/python
4. The script prints a JSON report. Do NOT recompute, estimate, or guess any of these numbers yourself.
5. Present the report to the user as a clear, readable summary: whether the files were joined (and on which column) or kept as separate sheets (and why), and where the result was saved. Make clear the original files were never modified.

## If subcommand is "analyze"

Tell the user this command is planned but not built yet, and suggest `/pandex clean <file>` or `/pandex gather <files>` instead.

## If no subcommand is recognized

Show usage: `/pandex clean <file>` or `/pandex gather <file1> <file2> ...` (analyze coming soon).
