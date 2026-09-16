# PandexAI — Visual Roadmap

A single-glance view of the whole project. See `03-Roadmap.md` for the detailed narrative history behind each item.

```mermaid
flowchart TD
    subgraph P0["Phase 0 — Foundation (COMPLETE)"]
        A1["✅ Naming & registration<br/>pandexai on npm/PyPI/GitHub"]:::done
        A2["✅ npx pandexai init<br/>auto-venv, SKILL.md, commands/"]:::done
        A3["✅ Judgment vs execution split<br/>proven end-to-end in Claude Code"]:::done
    end

    subgraph P1["Phase 1 — /pandex clean (COMPLETE)"]
        B1["✅ Diagnosis only: scan<br/>duplicates, blanks, casing, nulls"]:::done
        B2["✅ Renamed scan → clean<br/>real fixing behavior"]:::done
        B3["✅ Date + category standardization"]:::done
        B4["✅ Results folder:<br/>cleaned / duplicates / conflicts /<br/>missing_values / empty_rows"]:::done
        B5["✅ Reason columns + AutoFilter<br/>everywhere, always .xlsx"]:::done
        B1 --> B2 --> B3 --> B4 --> B5
    end

    subgraph P2["Phase 2 — /pandex gather (JUST BUILT)"]
        C1["✅ Join files on a real shared column<br/>(name match + value overlap)"]:::done
        C2["✅ Fallback: linked_sheets<br/>when no reliable connection exists"]:::done
        C3["🟠 Open question: should gather<br/>auto-clean messy inputs first?"]:::open
        C1 --> C2 --> C3
    end

    subgraph P3["Phase 3 — /pandex analyze (PLANNED)"]
        D1["🔵 Correlations, trends,<br/>group comparisons"]:::planned
    end

    subgraph P4["Idea stage — not started"]
        E1["🟣 /pandex validate<br/>business-rule checks"]:::idea
        E2["🟣 /pandex compare<br/>datasets or time periods"]:::idea
        E3["🟣 /pandex anomalies<br/>outliers, sudden spikes"]:::idea
    end

    subgraph SIDE["Parked / deferred"]
        F1["🟡 Measurement/unit standardization<br/>(kg vs lbs) — risky, deferred"]:::deferred
        F2["🟡 Public website"]:::deferred
        F3["🟡 README refresh for clean+gather"]:::deferred
        F4["🟡 Export to Notion/Power BI"]:::deferred
    end

    P0 --> P1 --> P2 --> P3 --> P4

    classDef done fill:#16302a,stroke:#3ddc97,color:#d7fff0
    classDef planned fill:#16233f,stroke:#5b8dff,color:#dce7ff
    classDef idea fill:#251a3f,stroke:#a374ff,color:#ecdcff
    classDef deferred fill:#332b14,stroke:#e0b94a,color:#fff2cf
    classDef open fill:#3a2016,stroke:#ff8a4a,color:#ffe4d4
    classDef default fill:#1c1f26,stroke:#4a5262,color:#e6e9ef

    style P0 fill:#14161c,stroke:#3a4152,color:#e6e9ef
    style P1 fill:#14161c,stroke:#3a4152,color:#e6e9ef
    style P2 fill:#14161c,stroke:#3a4152,color:#e6e9ef
    style P3 fill:#14161c,stroke:#3a4152,color:#e6e9ef
    style P4 fill:#14161c,stroke:#3a4152,color:#e6e9ef
    style SIDE fill:#14161c,stroke:#3a4152,color:#e6e9ef
```

## Legend
- ✅ **Done and published**
- 🔵 **Planned, not started**
- 🟣 **Idea stage, no design yet**
- 🟡 **Deliberately deferred**
- 🟠 **Open question, needs a decision**

## Current state (as of 2026-09-03)
- **`/pandex clean`** — feature-complete for this round. Results folder, reason columns, conflict detection, AutoFilter everywhere.
- **`/pandex gather`** — just built and published. Joins on a genuinely shared column (name + value overlap, not just name), or falls back to keeping files as separate sheets. Open question pending: should it auto-clean messy input files before joining, or require the user to run `clean` first?
- **`/pandex analyze`** — not started. Next natural candidate after `gather` settles.
