# PandexAI — Decision Log

Chronological record of the decisions made and why, so the reasoning isn't lost later.

## Naming (2026-08-28)

- **Brand:** PandexAI. **Package name:** `pandexai` (no hyphen), used identically on npm, PyPI, and GitHub.
- Plain `pandex` (no AI suffix) was rejected — it's a crowded name across ecosystems already (an existing PyPI `pandex` package, an Elixir/Hex `pandex`, a `pandex` GitHub org, unrelated repos). The `-ai` suffix avoids these collisions.
- Considered but not chosen: registering under a separate GitHub organization. Decision: use the user's own personal GitHub account instead.
- Domain `pandex.ai` is available but not free (~$60-90+/yr) — registration deferred along with the website work.

## Python environment strategy (2026-08-28) — LOCKED

Three options were considered for how `npx pandexai init` sets up Python dependencies:

- **Option A (rejected): pipx.** Breaks the "just run one command" simplicity the tool is going for.
- **Option B (CHOSEN): auto-venv on init.** Creates an isolated `.pandex/venv` inside the user's own project and installs dependencies there. Self-contained, no conflicts with the user's global Python setup, and works the same way across machines.
- **Option C (rejected): global pip install.** Risk of dependency version conflicts with whatever else is installed on the user's system.

## Working style constraint (2026-08-29) — MUST FOLLOW

The user is non-technical with low terminal comfort. Early in the project, Claude was writing/editing files directly via a connected-device bridge. The user explicitly and repeatedly asked for this to stop:

> "dont write anything yourself. write the script here i will add everything."
> "i want to do evrything in my terminal."

**Rule going forward:** Claude provides full file content and exact step-by-step terminal commands; the user executes everything themselves in their own terminal. (Documentation work in this Obsidian vault is a deliberate exception the user asked for separately — see the note at the bottom of this file.)

## Command structure (2026-08-30)

Single namespace decided: `/pandex <subcommand> [file]`. Behavior rule: no filename = operate on the last gathered dataset; filename given = operate on just that file. This came out of the user describing their real intended workflow — gather several files once, then run scan/analyze repeatedly without re-specifying files each time.

## Focus: harden `scan` before adding `gather`/`analyze` (2026-08-30)

User was offered four options for what to build next (more commands, connectors, polish scan, real slash-command integration) and chose to polish the existing `scan` command first. Reasoning that held throughout: every future command depends on the same file-reading and data-quality-check foundations, so bugs fixed here won't need to be re-fixed later in three different commands.

## Duplicate-value detection heuristic fix (2026-08-30)

Original design flagged a column as "should be unique" only if it was >90% unique overall. This is self-defeating on small datasets, because the duplicates being searched for are exactly what lowers the uniqueness ratio below the detection threshold. Fixed by adding a name-based override: any column with "id" in its name is always checked for duplicates regardless of its overall uniqueness ratio.

## Module split for `scripts/` (2026-08-30)

User raised a direct concern: "we have to update existing file more and more... if we use diff file we do not have to update file just we can create new file and add." Agreed and split the original single `profile.py` into `loaders.py` (file reading), `checks.py` (data-quality checks), and a thin `profile.py` orchestrator. This makes future features additive in most cases rather than requiring edits to one ever-growing file.

## Scope honesty conversation (2026-08-30)

Prompted by the user sharing a senior colleague's description of a real data analyst/data engineer job (BI dashboards, ETL pipelines, Snowflake, PySpark). Rather than overstating what PandexAI could do, agreed on an honest estimate: roughly 15-20% coverage of that full job, focused specifically on the file-based data cleaning/validation slice. Decided NOT to try to build ETL orchestration, live warehouse/ERP connections, or actual BI dashboards — those are different products at a different scale. Instead, the realistic path to "sharing results with a team" is exporting PandexAI's output to tools that already do that well (Notion, Power BI) rather than PandexAI building its own hosted multi-user product.

## Website (2026-08-29) — decided, but deferred

Decided PandexAI needs a public website eventually (branding/marketing/docs), modeled on how tools like Cursor, Claude Code, and OpenCode each have one. Explicitly deferred: core Phase 1 product work comes first, and no website research or building should start without the user's direct go-ahead (this was tested once when a WebFetch attempt was interrupted by the user for exactly this reason).

## Documentation in Obsidian (2026-08-30)

User asked for a complete, professional set of project documentation to be created and maintained in their Obsidian vault at `C:\Anik\Obsidian\PandexAI`, updated going forward whenever the code changes. This is a deliberate, explicit exception to the "don't write files directly" rule above — that rule was about the PandexAI codebase itself; documentation in the user's personal notes vault is a separate, explicitly requested deliverable.

## Rename scan to clean, add real fixing behavior (2026-08-31)

User mapped out what a real analyst's "clean data" step involves (fill missing values, remove duplicates, correct errors, standardize formats) and asked whether PandexAI's `scan` already did this. Answer: no — `scan` was diagnosis-only, it never modified data. User decided to rename `scan` to `clean` (not add a separate command) and have it actually apply fixes, on the reasoning that a single command doing both diagnosis and fixing is simpler for users than two.

Two follow-up decisions made explicitly with the user before building:
- **Numeric missing values:** fill with the column **median** (chosen over mean for being less skewed by outliers, over zero for being wrong in most contexts, and over leave-blank because the user wanted full cleaning, not partial).
- **Text/categorical missing values:** fill with the literal string **"Unknown"** (chosen over most-common-value fill, which risks quietly overstating the dominant category).

Safety principle applied throughout: `clean` never overwrites the original file — it always writes a new `<name>_cleaned.<ext>` file and reports exactly what changed, so nothing happens silently.

During testing, two real bugs were found and fixed (see `01-Architecture.md` for technical detail): a pandas 3.x dtype change that silently disabled casing/blank-normalization on all text columns, and a dedup-before-normalize ordering bug that missed near-duplicate rows. Both were caught specifically because the user insisted on testing every change against a real, deliberately messy CSV rather than trusting the code by inspection alone — validates the testing approach used throughout this project.
