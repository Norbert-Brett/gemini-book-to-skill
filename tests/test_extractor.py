import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from book_to_skill import utils
from book_to_skill.exceptions import ExtractionError


class TestExtractorCore(unittest.TestCase):
    def test_estimate_tokens_latin_and_cjk(self):
        self.assertEqual(utils.estimate_tokens(""), 0)
        latin = " ".join(["framework"] * 75)
        self.assertEqual(utils.estimate_tokens(latin), 100)
        cjk = "第一章系统设计原则与实践" * 30
        self.assertGreater(utils.estimate_tokens(cjk), 150)

    def test_detect_structure_numeric_and_toc(self):
        sample = (
            "Table of Contents\n"
            "Chapter 1: Reliable Systems\n"
            "Chapter 2: Consensus Models\n"
            "Chapter 3: Derived Data\n\n"
            "Chapter 1: Reliable Systems\n"
            + ("Reliability prose word. " * 120)
            + "\nChapter 2: Consensus Models\n"
            + ("Consensus prose word. " * 120)
            + "\nChapter 3: Derived Data\n"
            + ("Derived data prose word. " * 120)
        )
        info = utils.detect_structure(sample)
        self.assertTrue(info["has_toc"])
        self.assertEqual(info["chapters_detected"], 3)
        self.assertEqual(info["chapters_method"], "numeric")

    def test_detect_structure_markdown_headings(self):
        sample = (
            "# Architecture Overview\n"
            "## 1. Storage Engine\n" + ("word " * 100) + "\n"
            "## 2. Replication Log\n" + ("word " * 100) + "\n"
            "## 3. Partitioning\n" + ("word " * 100) + "\n"
        )
        info = utils.detect_structure(sample)
        self.assertGreaterEqual(info["chapters_detected"], 3)

    def test_extract_markdown_and_reuse_is_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            book_file = tmp_path / "sample_book.md"
            book_file.write_text(
                "# Designing Systems\n\n"
                "Table of Contents\n"
                "Chapter 1: Foundations\n"
                "Chapter 2: Replication\n\n"
                "Chapter 1: Foundations\n"
                "Use Fault Isolation when a subsystem can fail independently.\n\n"
                "Chapter 2: Replication\n"
                "Prefer Leader-Follower replication when strict ordering is required.\n",
                encoding="utf-8",
            )
            workdir = tmp_path / "work"
            env = os.environ.copy()
            env["BOOK_SKILL_WORKDIR"] = str(workdir)
            res = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "extract.py"), str(book_file), "--mode", "text", "--no-install-missing"],
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("Extraction complete:", res.stdout)
            meta_path = workdir / "metadata.json"
            text_path = workdir / "full_text.txt"
            self.assertTrue(meta_path.is_file())
            self.assertTrue(text_path.is_file())

            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            self.assertEqual(meta["filename"], "sample_book.md")
            self.assertEqual(meta["chapters_detected"], 2)
            cur_inputs = [(book_file, utils._sha256_file(str(book_file)))]
            ok, _ = utils.reuse_is_safe(cur_inputs, meta, "text")
            self.assertTrue(ok)
            ok_tech, _ = utils.reuse_is_safe(cur_inputs, meta, "technical")
            self.assertFalse(ok_tech)

            # Mutating the file invalidates the SHA-256 fingerprint
            book_file.write_text(book_file.read_text(encoding="utf-8") + "\nExtra line\n", encoding="utf-8")
            mutated_inputs = [(book_file, utils._sha256_file(str(book_file)))]
            ok_mutated, _ = utils.reuse_is_safe(mutated_inputs, meta, "text")
            self.assertFalse(ok_mutated)

    def test_extract_docx_stdlib_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "test.docx"
            with zipfile.ZipFile(docx_path, "w") as zf:
                zf.writestr(
                    "word/document.xml",
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                    "<w:body>"
                    "<w:p><w:r><w:t>Chapter 1: First Principles</w:t></w:r></w:p>"
                    "<w:p><w:r><w:t>Chapter 2: Mental Models</w:t></w:r></w:p>"
                    "</w:body></w:document>",
                )
            res = utils.extract_single_file(docx_path, "text", "no")
            self.assertIn("Chapter 1: First Principles", res["text"])
            self.assertIn("Chapter 2: Mental Models", res["text"])

    def test_prepare_output_dir_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            real_dir = tmp_path / "real"
            real_dir.mkdir()
            sym_dir = tmp_path / "sym"
            sym_dir.symlink_to(real_dir)
            with self.assertRaises(ExtractionError):
                utils.prepare_output_dir(sym_dir)

    def test_both_extract_entrypoints_support_check(self):
        for rel in ("scripts/extract.py", "skills/book-to-skill/scripts/extract.py"):
            proc = subprocess.run(
                [sys.executable, str(ROOT / rel), "--check"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("dependency check", proc.stdout)
            self.assertIn("gemini-book-to-skill", proc.stderr)


if __name__ == "__main__":
    unittest.main()
