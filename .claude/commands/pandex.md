---
description: Run PandexAI commands (clean, gather, analyze) for deterministic data profiling and cleaning
---

# Pandex

You are handling a `/pandex` command. The arguments passed are: $ARGUMENTS

Parse the first word as the subcommand, and everything after it as the filename(s) (if any).

## If subcommand is "clean"

1. Read SKILL.md and commands/clean.md in this project for full instructions.
2. If a filename was given, run: python scripts/clean.py <filename>
   If no filename was given, run: python scripts/clean.py (no arguments) -
   it will automatically clean whatever "/pandex gather" last produced in
   this project. If that also fails because nothing has been gathered yet,
   the script's error message will say so; relay it to the user plainly.
   Use the project's virtual environment Python, not the system one:
   - Windows: .pandex\venv\Scripts\python.exe
   - Mac/Linux: .pandex/venv/bin/python
3. The script prints a JSON report. Do NOT recompute, estimate, or guess any of these numbers yourself.
4. Present the report to the user as a clear, readable summary: what was changed, and list every file created inside the results folder. Make clear their original file was never modified. If "used_last_gathered_file" is present, say plainly which file that was, since the user didn't type it themselves.

## If subcommand is "gather"

1. Read SKILL.md and commands/gather.md in this project for full instructions.
2. If 2+ filenames were given, use them as-is. If exactly 1 was given, that's
   an error, relay the script's message (it needs at least 2). If no
   filenames were given at all, run gather with no arguments - it will
   auto-discover and combine every data file sitting in the project folder.
3. Run: python scripts/gather.py <file1> <file2> [file3 ...]
   or, with no filenames: python scripts/gather.py
   Use the project's virtual environment Python, not the system one:
   - Windows: .pandex\venv\Scripts\python.exe
   - Mac/Linux: .pandex/venv/bin/python
4. The script prints a JSON report. Do NOT recompute, estimate, or guess any of these numbers yourself.
5. Present the report to the user as a clear, readable summary: whether the files were joined (and on which column) or kept as separate sheets (and why), and where the result was saved. If "auto_discovered_files" is present, list exactly which files were found and used, since the user didn't type them themselves. Make clear the original files were never modified.

## If subcommand is "analyze"

Tell the user this command is planned but not built yet, and suggest `/pandex clean <file>` or `/pandex gather <files>` instead.

## If no subcommand is recognized

Show usage: `/pandex clean <file>` or `/pandex gather <file1> <file2> ...` (analyze coming soon).
