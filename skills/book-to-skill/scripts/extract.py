#!/usr/bin/env python3
"""
Entrypoint wrapper for book-to-skill inside skills/book-to-skill/scripts/extract.py.
Resolves the plugin repository root so `book_to_skill` can be imported cleanly
whether invoked from the skill directory or the plugin root.
"""

import sys
from pathlib import Path

if __name__ == "__main__":
    sys.dont_write_bytecode = True

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from book_to_skill.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
