---
description: Run PandexAI commands (clean, gather, analyze) for deterministic data profiling and cleaning
---

# Pandex

You are handling a `/pandex` command. The arguments passed are: $ARGUMENTS

Parse the first word as the subcommand, and everything after it as the filename (if any).

## If subcommand is "clean"

1. Read SKILL.md and commands/clean.md in this project for full instructions.
2. If no filename was given, tell the user a filename is required for now (`/pandex gather` is planned but not built yet).
3. Run: python scripts/clean.py <filename>
   Use the project's virtual environment Python, not the system one:
   - Windows: .pandex\venv\Scripts\python.exe
   - Mac/Linux: .pandex/venv/bin/python
4. The script prints a JSON report. Do NOT recompute, estimate, or guess any of these numbers yourself.
5. Present the report to the user as a clear, readable summary: what was changed, and the name of the new cleaned file that was created. Make clear their original file was never modified.

## If subcommand is "gather" or "analyze"

Tell the user this command is planned but not built yet, and suggest `/pandex clean <file>` instead.

## If no subcommand is recognized

Show usage: `/pandex clean <file>` (gather and analyze coming soon).
