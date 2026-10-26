#!/usr/bin/env bash
# scripts/install.sh
# Installs or links the Gemini Book to Skill plugin into Google Antigravity / Gemini discovery paths.
#
# Usage:
#   bash scripts/install.sh [--global | --workspace] [--check | --uninstall]
#
# Options:
#   --global     Install to ~/.gemini/config/plugins/gemini-book-to-skill (Default)
#   --workspace  Install to .agents/plugins/gemini-book-to-skill in current directory
#   --check      Verify installation without making changes
#   --uninstall  Remove the installed plugin symlink

set -euo pipefail

PLUGIN_NAME="gemini-book-to-skill"
SKILLS=(
    "book-to-skill"
)

if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
else
    REPO_ROOT="${HOME}/.gemini-book-to-skill"
fi

TARGET_SCOPE="global"
CHECK_ONLY=false
UNINSTALL=false

for arg in "$@"; do
    case "$arg" in
        --global)
            TARGET_SCOPE="global"
            ;;
        --workspace)
            TARGET_SCOPE="workspace"
            ;;
        --check)
            CHECK_ONLY=true
            ;;
        --uninstall)
            UNINSTALL=true
            ;;
        -h|--help)
            echo "Usage: $0 [--global | --workspace] [--check | --uninstall]"
            echo ""
            echo "Options:"
            echo "  --global     Install to ~/.gemini/config/plugins/${PLUGIN_NAME} (Default)"
            echo "  --workspace  Install to .agents/plugins/${PLUGIN_NAME} in current directory"
            echo "  --check      Verify installation without making any changes"
            echo "  --uninstall  Remove the installed plugin symlink"
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg"
            echo "Run '$0 --help' for usage."
            exit 1
            ;;
    esac
done

if [ "$TARGET_SCOPE" = "global" ]; then
    INSTALL_DIR="${HOME}/.gemini/config/plugins/${PLUGIN_NAME}"
else
    INSTALL_DIR="$(pwd)/.agents/plugins/${PLUGIN_NAME}"
fi

echo "==> Gemini Book to Skill Plugin Installer"
echo "    Source: $REPO_ROOT"
echo "    Target: $INSTALL_DIR (Scope: $TARGET_SCOPE)"
echo ""

if [ "$UNINSTALL" = true ]; then
    if [ -L "$INSTALL_DIR" ] || [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
        echo "✓ Uninstalled ${PLUGIN_NAME} from $INSTALL_DIR"
    else
        echo "✓ Nothing to uninstall at $INSTALL_DIR"
    fi
    exit 0
fi

verify_target() {
    local target="$1"
    if [ ! -d "$target" ] && [ ! -L "$target" ]; then
        return 1
    fi
    if [ ! -f "$target/plugin.json" ] || [ ! -f "$target/rules/AGENTS.md" ] || [ ! -f "$target/scripts/extract.py" ]; then
        return 1
    fi
    for s in "${SKILLS[@]}"; do
        if [ ! -f "$target/skills/$s/SKILL.md" ]; then
            return 1
        fi
    done
    return 0
}

if [ "$CHECK_ONLY" = true ]; then
    echo "Running preflight check..."
    if verify_target "$INSTALL_DIR"; then
        echo "✓ Installation verified: Plugin and book-to-skill are active at $INSTALL_DIR"
        exit 0
    else
        echo "✗ Not installed or incomplete at $INSTALL_DIR"
        exit 1
    fi
fi

# Ensure parent directory exists
PARENT_DIR="$(dirname "$INSTALL_DIR")"
mkdir -p "$PARENT_DIR"

# If destination exists and is already a symlink to this repo, report success
if [ -L "$INSTALL_DIR" ]; then
    CURRENT_LINK="$(readlink "$INSTALL_DIR")"
    if [ "$CURRENT_LINK" = "$REPO_ROOT" ]; then
        echo "✓ Already installed: $INSTALL_DIR is already linked to $REPO_ROOT"
        exit 0
    else
        echo "Updating existing symlink from $CURRENT_LINK to $REPO_ROOT..."
        rm "$INSTALL_DIR"
    fi
elif [ -d "$INSTALL_DIR" ]; then
    BACKUP="${INSTALL_DIR}.bak-$(date +%s)"
    echo "Warning: Existing non-symlink directory found at $INSTALL_DIR"
    echo "Backing up to $BACKUP..."
    mv "$INSTALL_DIR" "$BACKUP"
fi

echo "Creating symlink to plugin..."
ln -s "$REPO_ROOT" "$INSTALL_DIR"

echo "Verifying installation..."
if verify_target "$INSTALL_DIR"; then
    echo ""
    echo "✓ Success! Gemini Book to Skill plugin is installed at:"
    echo "  $INSTALL_DIR"
    echo ""
    echo "Antigravity and Gemini will now automatically discover book-to-skill and its rules."
else
    echo "✗ Error: Installation failed to verify target files."
    exit 1
fi
