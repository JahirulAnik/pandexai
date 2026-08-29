# PandexAI

AI-native data profiling CLI. PandexAI runs inside AI coding CLIs (Claude Code, Cursor, etc.) and handles the deterministic parts of data analysis - profiling columns, checking nulls, catching type issues - as real Python/pandas code, not AI guesses. The AI only handles judgment: interpreting results, flagging issues, and deciding what matters.

## Why


When working with an AI CLI on messy data, a lot of the groundwork does not need an LLM at all - it just needs pandas doing pandas things. PandexAI keeps that part deterministic and trustworthy, and lets the AI focus on the part that actually needs reasoning.

## Install

    npx pandexai init

This creates an isolated Python environment inside your project (`.pandex/venv`), installs pandas into it, and adds the files PandexAI needs (`SKILL.md`, `commands/`, `scripts/`).

## Usage

Inside your AI CLI session, ask it to scan a file:

    Please read SKILL.md and commands/scan.md, then run the scan command on yourfile.csv

The AI will run the real profiling script and give you column types, null percentages, unique counts, and stats - plus its own read on anything that looks off.

## Status

Early and actively developed. Currently supports one command: `scan`. More coming.

## License

MIT
