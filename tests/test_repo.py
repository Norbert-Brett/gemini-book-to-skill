import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
ABOUT = (
    "Turn any technical book, PDF, EPUB, DOCX, or documentation folder into a structured, "
    "on-demand Gemini and Google Antigravity skill with chapters, mental models, glossary, "
    "patterns, and cheatsheet. Free, MIT."
)


def frontmatter(path: Path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return (m.group(1) if m else ""), text


class TestRepoManifestsAndStructure(unittest.TestCase):
    def test_skill_folder_exists(self):
        found = sorted(
            d.name for d in SKILLS_DIR.iterdir()
            if d.is_dir() and (d / "SKILL.md").is_file()
        )
        self.assertEqual(found, ["book-to-skill"])

    def test_frontmatter_name_and_description(self):
        fm, text = frontmatter(SKILLS_DIR / "book-to-skill" / "SKILL.md")
        self.assertIn("name: book-to-skill\n", fm + "\n")
        self.assertRegex(fm, r"description: ")
        self.assertGreater(len(fm), 200)
        self.assertGreater(len(text.splitlines()), 150)

    def test_plugin_manifests_and_rules(self):
        plugin = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin["name"], "gemini-book-to-skill")
        self.assertEqual(plugin["description"], ABOUT)
        self.assertTrue((ROOT / plugin["logo"]).is_file())
        self.assertEqual(len(plugin["suggestedPrompts"]), 3)

        nested = json.loads(
            (ROOT / "plugins" / "gemini-book-to-skill" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(nested["name"], "gemini-book-to-skill")
        self.assertEqual(nested["description"], ABOUT)

        ext = json.loads((ROOT / "gemini-extension.json").read_text(encoding="utf-8"))
        self.assertEqual(ext["name"], "gemini-book-to-skill")
        self.assertEqual(ext["contextFileName"], "rules/GEMINI.md")

        self.assertTrue((ROOT / "rules" / "AGENTS.md").is_file())
        self.assertTrue((ROOT / "rules" / "GEMINI.md").is_file())
        self.assertTrue((ROOT / "scripts" / "install.sh").is_file())
        self.assertTrue((ROOT / "scripts" / "verify.sh").is_file())
        self.assertTrue((ROOT / "scripts" / "extract.py").is_file())
        self.assertTrue((SKILLS_DIR / "book-to-skill" / "scripts" / "extract.py").is_file())

    def test_readme_documents_plugin_and_inspiration(self):
        readme = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
        self.assertTrue(readme.startswith("# Gemini Book to Skill"))
        for section in (
            "## Overview",
            "## Quick Start & Installation",
            "bash scripts/install.sh",
            "## How to Use: Step-by-Step",
            "## Deterministic Python Tools",
            "## Supported Formats & Optional Extractors",
            "## License & Inspiration",
            "https://github.com/virgiliojr94/book-to-skill",
            "https://github.com/Norbert-Brett/gemini-book-to-skill.git",
        ):
            self.assertIn(section, readme)

    def test_installer_workspace_lifecycle(self):
        install_script = str(ROOT / "scripts" / "install.sh")
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Install in workspace mode
            res = subprocess.run(
                ["bash", install_script, "--workspace"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("Success!", res.stdout)
            target_link = Path(tmpdir) / ".agents" / "plugins" / "gemini-book-to-skill"
            self.assertTrue(target_link.is_symlink())
            self.assertEqual(target_link.resolve(), ROOT.resolve())

            # 2. Check workspace installation
            chk = subprocess.run(
                ["bash", install_script, "--workspace", "--check"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("Installation verified", chk.stdout)

            # 3. Uninstall workspace installation
            uninst = subprocess.run(
                ["bash", install_script, "--workspace", "--uninstall"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("Uninstalled", uninst.stdout)
            self.assertFalse(target_link.exists())


if __name__ == "__main__":
    unittest.main()
