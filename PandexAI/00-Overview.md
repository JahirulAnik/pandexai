# PandexAI — Project Overview

## What it is

**PandexAI** is an AI-native data profiling CLI. It runs inside AI coding CLIs (Claude Code, Cursor, and similar tools) and handles the deterministic parts of data analysis — profiling columns, checking nulls, catching type and duplicate issues — as real Python/pandas code, not AI guesses. The AI's role is limited to interpretation: flagging issues, summarizing results, and deciding what matters.

## Core architectural rule: judgment vs. execution

This is the non-negotiable rule the whole project is built around:

- **Execution (deterministic):** Anything that computes a number from data — a mean, a null count, a duplicate count — MUST run as real Python/pandas code. The AI is never allowed to estimate or guess a statistic that a script can compute exactly.
- **Judgment (AI):** Interpreting results, flagging likely issues, suggesting next steps, and writing a human-readable summary is the AI's job.

This split exists so PandexAI's numbers are always trustworthy — they come from real computation, never a language model's guess.

## Why it exists

When working with an AI CLI on messy data, a lot of the groundwork doesn't need an LLM at all — it just needs pandas doing pandas things. PandexAI keeps that part deterministic and trustworthy, and lets the AI focus on the part that actually needs reasoning.

## Branding

- **Brand name:** PandexAI
- **Package/technical name:** `pandexai` (no hyphen) — used identically across npm, PyPI, and GitHub
- **Positioning note:** name-adjacent to the existing library "PandasAI" — not a collision, just a possible source of confusion to be aware of in marketing copy.

## Links

- GitHub: https://github.com/jahirulanik/pandexai (public)
- npm: https://www.npmjs.com/package/pandexai
- PyPI: https://pypi.org/project/pandexai/

## Current status (as of 2026-08-30)

- **Phase 0 (Foundation):** Complete. Naming/registration, repo skeleton, core `scan` command, and packaging all proven end-to-end.
- **Phase 1 (Hardening `scan`):** In progress. Duplicate detection, core data-quality checks, and multi-file-format support (CSV/Excel/JSON) are done. Remaining: edge cases, large-file handling, better error messages, a test fixture set.
- **Future commands planned:** `gather` (combine multiple files), `analyze` (correlations/trends), and further out: `validate`, `compare`, `anomalies`.
- **Deferred, not started:** public website, domain registration, export integrations (Notion/Power BI), multi-user/hosted access.

See the other notes in this vault for architecture, command details, the full roadmap, and a running decision log.
