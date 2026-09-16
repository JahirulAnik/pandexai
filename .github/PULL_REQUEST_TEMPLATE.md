## What does this PR do?

<!-- One or two sentences. Link the issue if there is one: "Closes #123". -->

## Which command / area does it touch?

- [ ] `clean` (`scripts/clean.py`, `scripts/cleaner.py`)
- [ ] `gather` (`scripts/gather.py`, `scripts/gatherer.py`)
- [ ] `profile` (`scripts/profile.py`, `scripts/checks.py`)
- [ ] loaders / file formats (`scripts/loaders.py`)
- [ ] CLI installer (`bin/pandex.js`)
- [ ] AI-facing instructions (`SKILL.md`, `commands/*.md`, `.claude/commands/pandex.md`)
- [ ] docs / CI only

## Checklist

- [ ] `pytest` passes locally
- [ ] `ruff check scripts tests` passes
- [ ] I added or updated tests for behaviour I changed
- [ ] If the JSON report shape changed, I updated the matching `commands/*.md` file
- [ ] Numbers in the report come from real computation, never from the AI (see SKILL.md "Core rule")
- [ ] I did **not** bump the version (maintainers do that at release time)
