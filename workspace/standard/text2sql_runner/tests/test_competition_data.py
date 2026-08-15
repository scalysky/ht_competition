from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from workspace.standard.text2sql_runner.competition_data import (
    CompetitionQuestion,
    format_schema,
    load_questions,
)


class CompetitionQuestionTests(unittest.TestCase):
    def test_load_questions_discards_gold_sql(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "gold.json"
            source.write_text(
                json.dumps(
                    [{"id": 1, "question": "客户数量", "sql": "SELECT secret"}],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            questions = load_questions(source)

        self.assertEqual(
            questions,
            [CompetitionQuestion(id=1, question="客户数量")],
        )
        self.assertFalse(hasattr(questions[0], "sql"))

    def test_load_questions_rejects_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "gold.json"
            source.write_text(
                json.dumps(
                    [
                        {"id": 1, "question": "问题一", "sql": "SELECT 1"},
                        {"id": 1, "question": "问题二", "sql": "SELECT 2"},
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "题号重复"):
                load_questions(source)


class SchemaFormattingTests(unittest.TestCase):
    def test_format_schema_lists_columns_keys_and_foreign_keys(self) -> None:
        metadata = {
            "tables": [
                {
                    "name": "orders",
                    "columns": [
                        {
                            "name": "id",
                            "type": "bigint",
                            "nullable": False,
                            "ordinal_position": 1,
                        },
                        {
                            "name": "customer_id",
                            "type": "bigint",
                            "nullable": False,
                            "ordinal_position": 2,
                        },
                    ],
                    "primary_key": ["id"],
                }
            ],
            "foreign_keys": [
                {
                    "table": "orders",
                    "column": "customer_id",
                    "references_table": "customer",
                    "references_column": "id",
                }
            ],
        }

        text = format_schema(metadata)

        self.assertIn(
            "orders(id bigint NOT NULL, customer_id bigint NOT NULL)",
            text,
        )
        self.assertIn("PRIMARY KEY: orders.id", text)
        self.assertIn("FOREIGN KEY: orders.customer_id -> customer.id", text)

    def test_format_schema_rejects_empty_schema(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "未读取到 public schema"):
            format_schema({"tables": [], "foreign_keys": []})


if __name__ == "__main__":
    unittest.main()
