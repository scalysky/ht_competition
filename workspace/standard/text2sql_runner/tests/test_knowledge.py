from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from workspace.standard.text2sql_runner.knowledge import (
    combine_schema_and_knowledge,
    load_knowledge_context,
)


class KnowledgeContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / ".knowledge"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_full_recursively_loads_nonempty_markdown_in_relative_path_order(self) -> None:
        (self.root / "troubleshooting").mkdir(parents=True)
        (self.root / "architecture").mkdir(parents=True)
        (self.root / "architecture" / "b.md").write_text(
            "B表知识\n", encoding="utf-8"
        )
        (self.root / "architecture" / "a.md").write_text(
            "A表知识\n", encoding="utf-8"
        )
        (self.root / "troubleshooting" / "empty.md").write_text(
            " \n", encoding="utf-8"
        )
        (self.root / "ignored.txt").write_text("不得加载", encoding="utf-8")

        context = load_knowledge_context("Full", self.root)

        self.assertEqual(
            context.files,
            ("architecture/a.md", "architecture/b.md"),
        )
        self.assertEqual(
            context.content,
            "## 知识文件：architecture/a.md\n\nA表知识\n\n"
            "## 知识文件：architecture/b.md\n\nB表知识",
        )
        combined = combine_schema_and_knowledge("TABLE customer(id)", context)
        self.assertIn("TABLE customer(id)", combined)
        self.assertIn("A表知识", combined)
        self.assertNotIn("不得加载", combined)

    def test_none_does_not_require_or_read_knowledge_directory(self) -> None:
        missing_root = self.root / "does-not-exist"

        context = load_knowledge_context("None", missing_root)

        self.assertEqual(context.mode, "None")
        self.assertEqual(context.files, ())
        self.assertEqual(context.content, "")
        self.assertEqual(
            combine_schema_and_knowledge("TABLE customer(id)", context),
            "TABLE customer(id)",
        )

    def test_full_rejects_missing_or_empty_knowledge(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "知识库目录不存在"):
            load_knowledge_context("Full", self.root)

        self.root.mkdir(parents=True)
        (self.root / "empty.md").write_text("\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "没有非空 Markdown"):
            load_knowledge_context("Full", self.root)

    def test_rejects_unknown_mode(self) -> None:
        with self.assertRaisesRegex(ValueError, "知识库模式"):
            load_knowledge_context("Partial", self.root)


if __name__ == "__main__":
    unittest.main()
