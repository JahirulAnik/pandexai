---
description: Run PandexAI commands (scan, gather, analyze) for deterministic data profiling
---

# Pandex

You are handling a `/pandex` command. The arguments passed are: $ARGUMENTS

Parse the first word as the subcommand, and everything after it as the filename (if any).

## If subcommand is "scan"

1. Read SKILL.md and commands/scan.md in this project for full instructions.
2. If no filename was given, tell the user a filename is required for now (`/pandex gather` is planned but not built yet).
3. Run: python scripts/profile.py <filename>
   Use the project's virtual environment Python, not the system one:
   - Windows: .pandex\venv\Scripts\python.exe
   - Mac/Linux: .pandex/venv/bin/python
4. The script prints a JSON object. Do NOT recompute, estimate, or guess any of these numbers yourself.
5. Present the JSON results to the user as a clear, readable summary, and flag anything that looks like a data quality issue (high null %, suspicious types, low-cardinality columns that might be categorical).

## If subcommand is "gather" or "analyze"

Tell the user this command is planned but not built yet, and suggest `/pandex scan <file>` instead.

## If no subcommand is recognized

Show usage: `/pandex scan <file>` (gather and analyze coming soon).
