# PandexAI

PandexAI is an AI-native data profiling CLI. It runs inside AI coding CLIs
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

## Available commands

- scan - profiles a CSV file (columns, types, null %, unique counts, basic
  stats). See commands/scan.md for exact instructions.
