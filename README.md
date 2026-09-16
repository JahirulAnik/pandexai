# PandexAI

[![CI](https://github.com/jahirulanik/pandexai/actions/workflows/ci.yml/badge.svg)](https://github.com/jahirulanik/pandexai/actions/workflows/ci.yml)
[![npm](https://img.shields.io/npm/v/pandexai)](https://www.npmjs.com/package/pandexai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AI-native data cleaning CLI. PandexAI runs inside AI coding CLIs (Claude Code, Cursor,
etc.) and handles the deterministic parts of data work - deduplicating, normalising
casing and dates, filling blanks, joining files - as real Python/pandas code, not AI
guesses. The AI only handles judgment: reading the report, flagging what looks off,
and explaining it to you.

## Why

When working with an AI CLI on messy data, most of the groundwork doesn't need an LLM.
It needs pandas doing pandas things, exactly and repeatably. PandexAI keeps that half
deterministic and trustworthy, and lets the AI spend its effort on the half that
actually needs reasoning.

## Install

Inside your project:

```bash
npx pandexai init
```

This creates an isolated Python environment at `.pandex/venv`, installs pandas and
openpyxl into it, and copies the files the AI needs (`SKILL.md`, `commands/`,
`scripts/`, `.claude/`) into your project. Python 3.10+ and Node 18+ are required.

## Usage

In your AI CLI session:

```
/pandex clean sales.csv
/pandex gather sales.xlsx shipping_costs.xlsx
```

Any CSV, Excel (`.xlsx`/`.xls`) or JSON file works. **Your original files are never
modified.** Results are written to a folder next to the input.

### `clean <file>`

Diagnoses and cleans one file. It removes exact duplicate rows, standardises casing
("north" / "North"), turns blank-like text ("N/A", "-", "null") into real blanks, trims
whitespace, normalises dates to `YYYY-MM-DD`, maps known categories (M/male -> Male,
Y/yes -> Yes), and fills what's left (median for numbers, "Unknown" for text).

Creates `<file>_cleaned_results/` containing:

| File | When |
|---|---|
| `cleaned.xlsx` | Always. AutoFilter dropdowns on every column, auto-sized widths |
| `duplicates.xlsx` | Exact duplicate rows were found, with a `reason` column |
| `conflicts.xlsx` | Rows share an ID but differ elsewhere, with a `reason` column listing the differing fields |
| `missing_values.xlsx` | Some rows had blanks, with a `reason` column listing which fields |
| `empty_rows.xlsx` | Rows that were completely blank apart from the ID |

### `gather <file1> <file2> [...]`

Combines two or more files. It looks for a column whose **values** genuinely overlap
across all files (not just a shared name). If it finds one, it outer-joins on it so no
rows are lost. If it doesn't, it keeps each file as its own sheet in one workbook
rather than forcing a bad join. Creates `<file1>_gathered_results/gathered.xlsx`.

### `analyze`

Planned, not built yet.

## How it works

Each command is a small Python script that prints one JSON report. The markdown files
in `commands/` tell the AI how to run the script and which fields to present, and
forbid it from recomputing or estimating any number. See [CONTRIBUTING.md](CONTRIBUTING.md)
for the full architecture.

## Contributing

Issues and PRs are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) first: it covers
local setup, the test suite, CI, and the release process.

## License

MIT
