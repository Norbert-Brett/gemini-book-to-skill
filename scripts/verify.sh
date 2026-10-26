#!/usr/bin/env bash
# scripts/verify.sh
# Verification and test suite for the Gemini Book to Skill plugin.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "==> Verifying Gemini Book to Skill Plugin at: $REPO_ROOT"
ERRORS=0

# 1. Verify JSON manifests
echo "1. Checking JSON manifests..."
for json_file in "$REPO_ROOT/plugin.json" "$REPO_ROOT/plugins/gemini-book-to-skill/plugin.json" "$REPO_ROOT/gemini-extension.json"; do
    if [ -f "$json_file" ]; then
        if python3 -m json.tool "$json_file" > /dev/null 2>&1; then
            echo "  ✓ Valid JSON: ${json_file#$REPO_ROOT/}"
        else
            echo "  ✗ INVALID JSON: ${json_file#$REPO_ROOT/}"
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo "  ✗ Missing JSON file: ${json_file#$REPO_ROOT/}"
        ERRORS=$((ERRORS + 1))
    fi
done

# 2. Verify Skill and Frontmatter via validate_skill.py
echo "2. Checking book-to-skill SKILL.md and frontmatter..."
SKILL_FILE="$REPO_ROOT/skills/book-to-skill/SKILL.md"
if [ -f "$SKILL_FILE" ]; then
    if python3 "$REPO_ROOT/tools/validate_skill.py" --lens gemini "$SKILL_FILE" > /dev/null 2>&1; then
        echo "  ✓ Valid skill & frontmatter (gemini lens): skills/book-to-skill/SKILL.md"
    else
        echo "  ✗ Invalid skill frontmatter: skills/book-to-skill/SKILL.md"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "  ✗ Missing skill file: skills/book-to-skill/SKILL.md"
    ERRORS=$((ERRORS + 1))
fi

# 3. Verify Rules, Tools & Assets
echo "3. Checking rules, tools, assets, and documentation..."
REQUIRED_FILES=(
    "rules/AGENTS.md"
    "rules/GEMINI.md"
    "assets/logo.svg"
    "scripts/extract.py"
    "skills/book-to-skill/scripts/extract.py"
    "tools/discovery_tax.py"
    "tools/scan_generated_skill.py"
    "tools/validate_skill.py"
    "README.md"
    "LICENSE"
)

for req in "${REQUIRED_FILES[@]}"; do
    if [ -f "$REPO_ROOT/$req" ]; then
        echo "  ✓ Exists: $req"
    else
        echo "  ✗ Missing file: $req"
        ERRORS=$((ERRORS + 1))
    fi
done

# 4. Verify Shell Scripts syntax
echo "4. Checking shell scripts syntax..."
for scr in "scripts/install.sh" "scripts/verify.sh"; do
    if [ -f "$REPO_ROOT/$scr" ]; then
        if bash -n "$REPO_ROOT/$scr"; then
            echo "  ✓ Bash syntax clean: $scr"
        else
            echo "  ✗ Bash syntax errors in $scr"
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo "  ✗ Missing script: $scr"
        ERRORS=$((ERRORS + 1))
    fi
done

# 5. Run Python Unit Test Suite
echo "5. Running Python unit test suite..."
if python3 -m unittest discover -s "$REPO_ROOT/tests" -v; then
    echo "  ✓ Python unit tests passed"
else
    echo "  ✗ Python unit tests FAILED"
    ERRORS=$((ERRORS + 1))
fi

echo ""
if [ "$ERRORS" -eq 0 ]; then
    echo "==> ALL CHECKS PASSED! Gemini Book to Skill plugin is healthy."
    exit 0
else
    echo "==> FAILED with $ERRORS error(s)."
    exit 1
fi
