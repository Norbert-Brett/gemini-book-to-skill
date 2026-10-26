# Gemini Book to Skill Operating Rules

When the Gemini Book to Skill plugin is active, Antigravity and Gemini agents have access to the `book-to-skill` converter skill and three deterministic Python tools (`scripts/extract.py`, `tools/scan_generated_skill.py`, and `tools/validate_skill.py`).

## 1. Architecture & Separation of Concerns
- **Deterministic Extraction (`scripts/extract.py` -> `book_to_skill/`)**: Always extract document text, chapter counts, SHA-256 source fingerprints, and token estimates via `scripts/extract.py` into a per-run isolated workdir (`<tempdir>/book_skill_work-<pid>/`). Never guess page counts or token numbers by hand.
- **Spec-Driven Skill Generation (`skills/book-to-skill/SKILL.md`)**: Follow the four modes in `SKILL.md` (Full Conversion, Analyze Only, Generate from Prior Analysis, and Update / Fold-in) to distill books and documentation into structured, progressive-disclosure skills:
  - `SKILL.md` (core frameworks + chapter/topic index, <= 4,000 tokens)
  - `chapters/ch<NN>-<slug>.md` (loaded on demand)
  - `glossary.md`, `patterns.md`, and `cheatsheet.md`

## 2. Antigravity & Cross-Agent Skill Destinations
- **Personal / Global Scope (Default)**: Write generated book skills to `~/.agents/skills/<skill_name>/` and create a verified symlink at `~/.gemini/config/skills/<skill_name>` (and `~/.claude/skills/<skill_name>` if requested) so Google Antigravity, Gemini CLI, and cross-agent hosts discover the generated skill automatically.
- **Project / Workspace Scope**: When the user asks for project-local output (or sets `BOOK_TO_SKILL_SCOPE=project`), write the generated skill to `.agents/skills/<skill_name>/` in the active workspace.
- **Subagent Acceleration for Large Books**: For books with many chapters, Antigravity agents may dispatch parallel subagents in waves using `invoke_subagent` (`TypeName: "self"`, `Model: "flash"` or `"inherit"`) to summarize slice ranges of `full_text.txt` into `chapters/ch<NN>-<slug>.md` concurrently.

## 3. Security, Integrity & Copyright Guardrails
- **Advisory Security Scan**: Always run `python3 tools/scan_generated_skill.py <skill_dir>` (and `python3 tools/validate_skill.py --lens gemini <skill_dir>/SKILL.md`) before reporting completion or publishing.
- **Synthesize, Never Copy Raw Text**: Capture named frameworks, decision rules, techniques, and anti-patterns in practitioner voice. Never copy raw copyrighted passages verbatim.
- **Private-by-Default Publishing**: When publishing a generated skill to GitHub (`Step 11`), always default to `--private`. Skills derived from third-party copyrighted books must remain private.
