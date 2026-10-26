---
name: book-to-skill
description: "Converts books and documents (PDF, EPUB, DOCX, HTML, Markdown, plain text, RTF, MOBI/AZW with Calibre) into structured agent skills, extracting frameworks, mental models, principles, techniques, and anti-patterns. Use when the user wants to study a book or document in Google Antigravity, Gemini CLI, or any Agent Skills host, apply an author's frameworks while working, or build a reusable knowledge base from files."
---

# Book-to-Skill Converter (Google Antigravity & Gemini Edition)

Transform written knowledge into actionable agent skills by extracting structure, not producing summaries.

## Philosophy

Books and technical documents contain crystallized expertise: frameworks, principles, and techniques that took years to develop. This skill extracts that knowledge into an on-demand format that **Google Antigravity**, **Gemini CLI**, and any open Agent Skills host can leverage repeatedly without blowing up your context window.

**Extract structure, not summaries.** A skill is not a book report. It is a practitioner's toolkit of:
- Named frameworks (mental models with clear application)
- Actionable principles (rules that guide decisions)
- Techniques (step-by-step methods)
- Anti-patterns (what to avoid and why)
- Voice calibration (how the author thinks and communicates)

**Preserve the author's precision.** Frameworks have specific names for reasons. "The 5 Whys" is not interchangeable with "ask why multiple times." Capture the exact formulation.

**Layer depth appropriately.** Simple books produce simple skills. Complex books with 10+ frameworks produce skills with reference files and on-demand chapters.

---

## Modes of Operation

Four paths are available. Route based on what the user asks:

### 1. Full Conversion (Default)
- **Trigger**: User provides one or more document, directory, or glob paths without special instructions.
- **Action**: Run all steps below (Steps 0 through 10, plus optional Step 11).
- **Output**: Complete skill with `SKILL.md`, `chapters/`, `glossary.md`, `patterns.md`, and `cheatsheet.md`.

### 2. Analyze Only
- **Trigger**: User says "analyze", "just extract", or "I want to review before generating".
- **Action**: Run Steps 0 through 3, then produce a structured extraction report (frameworks, principles, techniques, and chapters found). Stop and do NOT generate skill files yet.
- **Output**: Analysis report for user review.

### 3. Generate from Prior Analysis
- **Trigger**: User has existing analysis notes or previously ran Analyze Only.
- **Action**: Skip Steps 0 through 3, use the provided analysis as input, and run Steps 4 through 10.
- **Output**: Skill files generated from the prior analysis.

### 4. Update / Fold-in (Existing Skill)
- **Trigger**: User provides one or more new source paths and indicates they want to update an existing skill (either by pointing to the existing skill folder, providing a skill slug that already exists in `SKILLS_HOME`, or explicitly requesting an update).
- **Action**: Run Step 0 (out-of-scope check), Step 1 (validate inputs), Step 1.5 (identify book type), and Step 2 (extract new files). Then skip to Step 5 (resolve existing skill path) and run the **Update / Fold-in Workflow** to merge the new content into the existing skill files.
- **Output**: Updated existing skill with new or revised chapter summaries and merged indexes, glossary, patterns, and cheatsheet.

---

## Skill Locations & Discovery

In **Google Antigravity** and **Gemini**, skills and plugins are discovered from:
1. **Google Antigravity / Gemini Global Plugin**: `~/.gemini/config/plugins/gemini-book-to-skill/`
2. **Google Antigravity / Gemini Workspace Plugin**: `.agents/plugins/gemini-book-to-skill/`
3. **Google Antigravity / Gemini Global Skills**: `~/.gemini/config/skills/`
4. **Workspace / Project-Local Skills** (Antigravity, Gemini, Amp, Copilot, Codex, OpenCode): `.agents/skills/`
5. **Cross-Agent Personal Skills Hub**: `~/.agents/skills/`

For **generated** book skills:
- **Personal / Global scope (Default)**: Write the generated skill to `~/.agents/skills/<skill_name>/` and create a verified symlink at `~/.gemini/config/skills/<skill_name>` (in Step 10) so both **Google Antigravity / Gemini** and cross-agent hosts discover it automatically from a single copy on disk.
- **Project / Workspace scope**: When the user asks to save the skill inside the current project (or sets `BOOK_TO_SKILL_SCOPE=project`), write directly to `.agents/skills/<skill_name>/` in the workspace root, which Antigravity discovers natively.

---

## Step 0: Out-of-Scope Check & Re-run Guard

If no arguments or document paths are provided, stop and respond:
> "`book-to-skill` requires a supported document path, folder, or glob pattern. Usage: `book-to-skill <path-to-document-folder-or-glob>... [skill-name-slug]`"

Throughout the workflow:
- **Resolve the destination root first.** Before any existing-skill lookup, determine where this run will write: the personal root (`~/.agents/skills` / `~/.gemini/config/skills`) or the project-local root (`.agents/skills`) per Step 5.
- Identify the input paths and the optional skill slug:
  - If the last argument is not an existing file, folder, or matching glob, and looks like a skill slug (lowercase hyphens, alphanumeric), treat it as `SKILL_NAME`.
  - Treat all other arguments as `INPUT_PATHS`.
- If any input path is an existing skill directory (contains `SKILL.md` and `chapters/`), or if `SKILL_NAME` matches an existing skill slug in the resolved root, flag this run as an **Update / Fold-in** operation (Mode 4).
- **Re-run guard.** Before starting extraction for a Full Conversion, derive the prospective skill slug under Step 5's naming options (author-concept form, by-title form, and any `SKILL_NAME` given) and check the resolved root (`~/.agents/skills`, `~/.gemini/config/skills`, or `.agents/skills`). On a match, STOP and ask the user:
  > "`<skill-name>` already exists. Choose: (1) Update / Fold-in (Mode 4), (2) verify the existing skill is complete and stop, or (3) force full regeneration."
- **Context recovery reuse.** After an interrupted run, reuse the extraction work directory (`Workdir ->` in its output, or `BOOK_SKILL_WORKDIR`) **only if it is still intact and still matches the current inputs and options**: `metadata.json` is readable, its `sources` match the current files one-to-one on filename **and content fingerprint** (`sha256`, checked via `reuse_is_safe()` in `book_to_skill/utils.py`), and `extraction_mode` matches. Otherwise start a fresh extraction.

---

## Step 1: Validate Input

Verify that there is at least one supported file, directory, or glob pattern among `INPUT_PATHS`.
Supported formats: `.pdf`, `.epub`, `.docx`, `.txt`, `.text`, `.md`, `.markdown`, `.rst`, `.adoc`, `.asciidoc`, `.html`, `.htm`, `.xhtml`, `.rtf`, `.mobi`, `.azw`, `.azw3`.

If no supported files are found, stop with a clear error message.

---

## Step 1.5: Identify Content Type

Before extracting, ask the user (using `ask_question` if available, or inline text):

> "What kind of content do these sources have? This helps choose the best extraction method:
> 1. **Technical** — has code blocks, tables, formulas, or architecture diagrams (`BOOK_TYPE=technical`)
> 2. **Text-heavy** — mostly prose, management, strategy, or narrative non-fiction (`BOOK_TYPE=text`)
> 3. **Not sure** — use the fast text extractor (`BOOK_TYPE=text`)"

- If `BOOK_TYPE=technical`: inform the user that Docling structure-aware extraction will be used when installed (falling back to the PDF text chain if unavailable).
- If `BOOK_TYPE=text`: inform the user that the fastest suitable extractor will be used for each format.

---

## Step 2: Extract Text from the Source Documents

Locate and run `extract.py` from the plugin or workspace:

```bash
SCRIPT_PATH=""
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

CANDIDATES=(
  "$HOME/.gemini/config/plugins/gemini-book-to-skill/scripts/extract.py"
  "$PROJECT_ROOT/.agents/plugins/gemini-book-to-skill/scripts/extract.py"
  "$PROJECT_ROOT/scripts/extract.py"
  "$HOME/.gemini/config/skills/book-to-skill/scripts/extract.py"
  "$PROJECT_ROOT/.agents/skills/book-to-skill/scripts/extract.py"
  "$HOME/.agents/skills/book-to-skill/scripts/extract.py"
  "$HOME/.claude/skills/book-to-skill/scripts/extract.py"
  "$HOME/.copilot/skills/book-to-skill/scripts/extract.py"
  "scripts/extract.py"
)

for candidate in "${CANDIDATES[@]}"; do
  if [ -f "$candidate" ]; then
    SCRIPT_PATH="$candidate"
    break
  fi
done

if [ -z "$SCRIPT_PATH" ]; then
  echo "Could not find scripts/extract.py for gemini-book-to-skill" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" "$SCRIPT_PATH" $INPUT_PATHS --mode <BOOK_TYPE> --install-missing no
```

> **Tip — Preflight Environment Check**: Run `"$PYTHON_BIN" "$SCRIPT_PATH" --check` to print a per-format report of which optional extractors (`pypdf`, `pdfminer.six`, `pdftotext`, `docling`, `ebooklib`, `python-docx`, `trafilatura`, `striprtf`, `ebook-convert`) are installed and the exact command to install any missing ones.

This creates a **per-run** work directory (`<tempdir>/book_skill_work-<pid>/` by default, or `BOOK_SKILL_WORKDIR`) containing:
- `full_text.txt` — combined, sanitized extracted text of all sources with `SOURCE:` boundaries.
- `metadata.json` — combined size, words, pages, token counts, SHA-256 fingerprints, detected chapter count, chapter heading samples, `workdir`, and per-source details.

Always read `metadata.json` from the `Meta ->` path printed by the command and confirm the extracted `filename` / `sources` match the document you asked for.

---

## Step 2.5: Pre-Flight Token & Time Estimate

Read `metadata.json` and present a concise summary before generating skill files:

```text
Sources detected: <total_sources> source(s) (<filenames>)
Combined Pages/Sections: ~<N> | Words: ~<N> | Source Tokens: ~<N>K | Chapters Detected: <N>

Estimated Token Budget (Full Conversion / Update):
  Input (reading + chapter prompts): ~<N>K tokens
  Output (SKILL.md + chapters + glossary + patterns + cheatsheet): ~<N>K tokens

Proceed with Full Conversion / Update? (or reply "analyze only" to preview frameworks first)
```

---

## Step 2.6: Targeted Access for Large Books (> 50k Tokens)

Treat `full_text.txt` as a queryable corpus rather than loading the entire file into context at once. For books over ~50k tokens:
- Use `grep -n` to find chapter line offsets in `full_text.txt`:
  ```bash
  grep -n -E "^\s*(Chapter|CHAPTER|Part|PART|#)\s+" "$FULL_TEXT_PATH" | head -60
  ```
- Read only the specific line range for each chapter using `read_file` (`StartLine` / `EndLine`) or `sed -n '<start>,<end>p' "$FULL_TEXT_PATH"`.

---

## Step 3: Analyze Book Structure

Read the front matter and Table of Contents of `full_text.txt` (plus `chapter_headings_sample` in `metadata.json`) to identify:
- Book **title** and **author(s)**
- **Chapter list** (numbers, titles, and line ranges in `full_text.txt`)
- **Core themes** and subject domain

**If mode is "Analyze Only" (Mode 2)**: produce the structured Extraction Report (Author's Core Frameworks, Key Principles, Techniques & Methods, Anti-patterns, Suggested Skill Name, and Chapters Table) and stop here.

---

## Step 4: Ask Purpose & Derive Depth (Full Conversion Only)

Ask the user what the skill should prioritize:
1. **Apply the author's frameworks while working**
2. **Think with the author's mental models**
3. **Reference specific chapters and concepts**
4. **All of the above**

Derive `DEPTH` automatically from the answer:
- Answer is **only** option 3 (reference) -> `DEPTH=reference` (lean, fast-lookup chapters).
- Answer includes option 1, 2, or 4 -> `DEPTH=study` (includes a concrete `## Worked Example` and expanded step-by-step framework guidance in each chapter).

---

## Step 5: Determine Skill Name & Destination (`SKILLS_HOME`)

If `SKILL_NAME` was not provided, propose two slug options:
- **By author-concept**: `{author-lastname}-{core-concept}` (e.g., `kleppmann-data-intensive`, `cialdini-influence`)
- **By title**: lowercase hyphenated title (e.g., `designing-data-intensive-apps`)

Resolve the destination directory (`SKILLS_HOME`):

| Scope | Primary Write Directory (`SKILLS_HOME`) | Antigravity / Host Discovery Link |
| :--- | :--- | :--- |
| **Personal / Global (Default)** | `~/.agents/skills/<skill_name>` | Symlinked to `~/.gemini/config/skills/<skill_name>` (and `~/.claude/skills/<skill_name>` if present) in Step 10 |
| **Project / Workspace (`BOOK_TO_SKILL_SCOPE=project`)** | `.agents/skills/<skill_name>` | Discovered natively by Google Antigravity, Gemini CLI, and cross-agent hosts |

If `$SKILLS_HOME/<skill_name>/` already exists, prompt the user to choose:
1. **Update / Fold-in** (Mode 4)
2. **Overwrite**
3. **Rename**

---

## Step 6: Create Skill Directory Structure

```bash
mkdir -p "$SKILLS_HOME/<skill_name>/chapters"
```

---

## Step 7: Generate Chapter Summaries

Scale each chapter file to the token budget matrix:

| Content Type | `DEPTH=reference` | `DEPTH=study` |
| :--- | :--- | :--- |
| `BOOK_TYPE=text` | 800 - 1,200 tokens | 1,000 - 1,800 tokens |
| `BOOK_TYPE=technical` | 1,200 - 1,800 tokens | 2,000 - 3,000 tokens |

> **Antigravity Subagent Acceleration**: For books with 8+ chapters, you may dispatch subagents in parallel waves (up to 8 at a time) using `invoke_subagent` (`TypeName: "self"`, `Model: "flash"` or `"inherit"`), passing each subagent its assigned chapter's line range in `full_text.txt` and target output path `$SKILLS_HOME/<skill_name>/chapters/ch<NN>-<slug>.md`.

Each chapter file (`$SKILLS_HOME/<skill_name>/chapters/ch<NN>-<slug>.md`) must follow this structure:

```markdown
# Chapter N: <Full Title>

## Core Idea
<1-2 sentences: the single most important thing this chapter teaches>

## Frameworks Introduced
- **<Framework Name>**: <exact formulation — preserve the author's naming>
  - When to use: <specific situation>
  - How: <explicit steps or criteria>

## Key Concepts
- **<Term>**: <precise definition in 1 sentence>

## Mental Models
<2-4 frameworks or thinking tools written as "Use X when Y" or "Think of X as Y">

## Anti-patterns
- **<What to avoid>**: <why it fails>

## Code Examples *(technical books only — omit if BOOK_TYPE=text)*
```<language>
<key instructive snippet from this chapter>
```
- **What it demonstrates**: <one line>

## Reference Tables *(technical books only — omit if BOOK_TYPE=text)*
<Comparison matrix, parameter table, or decision table in markdown>

## Worked Example *(DEPTH=study only — omit for DEPTH=reference)*
<Reconstruct one concrete example, decision walk-through, or before/after from the chapter compactly in your own synthesized words — never copy raw passages>

## Key Takeaways
1. <Actionable insight>
2. <Actionable insight>
3. <Actionable insight>

## Connects To
- **Ch N**: <how this chapter relates>
```

---

## Step 8: Generate Supporting Files

1. **`$SKILLS_HOME/<skill_name>/glossary.md`** (max ~1,500 tokens):
   - Every significant term from the book, alphabetically sorted:
     `**Term** — concise definition (Ch N)`
2. **`$SKILLS_HOME/<skill_name>/patterns.md`** (max ~2,000 tokens):
   - All concrete techniques, design patterns, and algorithms:
     `## Pattern Name\n- **When to use**: ...\n- **How**: ...\n- **Trade-offs**: ...`
3. **`$SKILLS_HOME/<skill_name>/cheatsheet.md`** (max ~1,200 tokens):
   - High-density reasoning aid capturing the author's judgment:
     - **Decision rules** ("When X, do Y, because Z")
     - **Decision trees / Trade-off matrices**
     - **Thresholds & rules of thumb**
     - **Tells & smells** ("If you see X, you are likely hitting problem Y")

---

## Step 9: Generate the Master `SKILL.md`

**CRITICAL TOKEN BUDGET**: Keep the master `SKILL.md` under **4,000 tokens** and front-load the most important frameworks first.

Create `$SKILLS_HOME/<skill_name>/SKILL.md`:

```markdown
---
name: <skill_name>
description: "Knowledge base from \"<Full Title>\" by <Author(s)>. Use when applying <author>'s frameworks for <key topics, 3-6 terms>, studying the book, or referencing its concepts."
---

# <Full Title>
**Author**: <Author(s)> | **Pages**: ~<N> | **Chapters**: <N> | **Generated**: <YYYY-MM-DD>

## How to Use This Skill

- **Overview** — apply the Core Frameworks below directly while working
- **Topic lookup** — check the Topic Index below and read the matching `chapters/ch<NN>-<slug>.md` file on demand
- **Chapter deep-dive** — read `chapters/ch<NN>-<slug>.md` for worked examples and details
- **Quick decisions** — read `cheatsheet.md`, `patterns.md`, or `glossary.md`

---

## Core Frameworks & Mental Models
<~2,000 tokens of the author's most critical named frameworks, principles, and decision rules. Write as "Use X when Y", "Prefer X over Y because Z".>

---

## Chapter Index

| # | Title | Key Frameworks |
| :--- | :--- | :--- |
| [ch01](chapters/ch01-<slug>.md) | <Title> | <framework1>, <framework2> |
| [ch02](chapters/ch02-<slug>.md) | <Title> | <framework1>, <framework2> |

## Topic Index

- **<Term or Topic>** -> ch<NN>[, ch<NN>]

## Supporting Files

- [glossary.md](glossary.md) — alphabetical definitions of key terms
- [patterns.md](patterns.md) — concrete techniques, patterns, and trade-offs
- [cheatsheet.md](cheatsheet.md) — decision rules, thresholds, and trade-off tables

---

## Scope & Limits

Synthesized knowledge skill derived from *<Full Title>*. Chapter files are loaded on demand to keep context usage low.
```

---

## Step 9.5: Scan & Validate the Generated Skill

Run the advisory security scanner and the `gemini` skill validator before linking or reporting completion:

```bash
SKILL_CONVERTER_ROOT="$(cd "$(dirname "$SCRIPT_PATH")/.." && pwd)"
if [ ! -d "$SKILL_CONVERTER_ROOT/tools" ]; then
  SKILL_CONVERTER_ROOT="$(cd "$(dirname "$SCRIPT_PATH")/../../.." && pwd)"
fi

"$PYTHON_BIN" "$SKILL_CONVERTER_ROOT/tools/scan_generated_skill.py" "$SKILLS_HOME/<skill_name>"
"$PYTHON_BIN" "$SKILL_CONVERTER_ROOT/tools/validate_skill.py" --lens gemini "$SKILLS_HOME/<skill_name>/SKILL.md"
```

If `scan_generated_skill.py` or `validate_skill.py` exits non-zero, review and resolve the reported lines before proceeding.

---

## Step 10: Link for Google Antigravity / Gemini, Cleanup & Report

For **Personal / Global** installs (`SKILLS_HOME="$HOME/.agents/skills"`), link the generated skill into Google Antigravity's global skills directory (`~/.gemini/config/skills/<skill_name>`) so Antigravity and Gemini CLI discover it automatically:

```bash
mkdir -p "$HOME/.gemini/config/skills"
GEMINI_LINK="$HOME/.gemini/config/skills/<skill_name>"
TARGET="$HOME/.agents/skills/<skill_name>"
if [ ! -e "$GEMINI_LINK" ] || [ -L "$GEMINI_LINK" ]; then
  ln -sfn "$TARGET" "$GEMINI_LINK"
fi
```

Then remove the per-run extraction workdir (`Workdir ->` from `metadata.json`):

```bash
rm -rf "$WORKDIR"
```

Report the completed skill to the user:

```text
Skill created: $SKILLS_HOME/<skill_name>/
Linked for Google Antigravity & Gemini: ~/.gemini/config/skills/<skill_name> (or .agents/skills/<skill_name> for workspace installs)

Book: <Full Title> — <Author>
Pages: ~<N> | Chapters: <N>

Files generated:
  SKILL.md       — core frameworks + chapter/topic index (~X tokens)
  chapters/      — <N> on-demand chapter files (~X tokens each)
  glossary.md    — alphabetical key terms (~X tokens)
  patterns.md    — techniques & patterns (~X tokens)
  cheatsheet.md  — decision rules & trade-off tables (~X tokens)
```

---

## Step 11: Publish the Generated Skill to GitHub (Optional)

Only if Step 9.5 passed, you may offer once:
> "Would you like to publish this generated skill to a GitHub repository? (yes / skip)"

- **Visibility Gate (Strict Rule)**: Ask as a separate closed question:
  > "Private or public repository? Reply with one word: `private` or `public`."
  - Always run `gh repo create <repo_name> --private --source . --push` unless the user's reply to the visibility question is the bare word `public` (substring matching is forbidden; statements like "the book is in the public domain" are licence descriptions, not visibility answers, and must resolve to `--private`).
- **Copyright Gate**: Skills generated from third-party copyrighted books must remain **private**. Only allow `--public` when the source is the user's own writing, openly licensed documentation, or public-domain material.
- **Nested-Repo Guard**: If `$SKILLS_HOME/<skill_name>` is inside an existing git worktree (such as `.agents/skills/<skill_name>`), copy it to a temporary directory before running `git init` so you do not create an embedded gitlink inside the outer repository.

---

## Update / Fold-in Workflow (Mode 4)

When updating an existing skill at `$SKILLS_HOME/<skill_name>/`:
1. **Read Existing Skill Structure**: Inspect `$SKILLS_HOME/<skill_name>/SKILL.md`, list `chapters/` to find the highest chapter number, and read `glossary.md`, `patterns.md`, and `cheatsheet.md`.
2. **Match Content**: Compare the newly extracted `full_text.txt` against existing chapters to identify **revisions to existing chapters** vs. **new chapters** (numbered sequentially after the highest existing `ch<NN>`).
3. **Write Chapter Files**: Update revised chapter files and create new `chapters/ch<NN>-<slug>.md` files following Step 7.
4. **Merge Supporting Files**: Merge and alphabetize new terms into `glossary.md`, append new patterns to `patterns.md`, and integrate new decision rules into `cheatsheet.md`.
5. **Update Master `SKILL.md`**: Update chapter/page counts, `Generated` date, Core Frameworks (keeping total body <= 4,000 tokens), Chapter Index, and Topic Index.
6. **Scan, Validate & Cleanup**: Run Step 9.5 (`scan_generated_skill.py` and `validate_skill.py --lens gemini`) and Step 10 cleanup.

---

## Quality Rules

1. **Extract structure, not summaries** — capture named frameworks, exact formulations, decision rules, and anti-patterns.
2. **Preserve the author's precision** — keep exact framework names and terminology.
3. **Density over completeness** — a 1,000-token structured chapter beats a 10,000-token raw excerpt.
4. **Practitioner voice** — write "Use X when Y", not "In this chapter the author discusses X".
5. **Front-load `SKILL.md`** — put Core Frameworks before indexes so the highest-leverage knowledge is always read first.
6. **Chapter files are on-demand** — keep detailed examples inside `chapters/ch<NN>-<slug>.md` so they cost zero tokens until needed.
7. **Never copy raw book text** — always synthesize and reconstruct in your own words.
8. **Topic index is critical** — map every key concept to its chapter file so the agent can route questions in one hop.
