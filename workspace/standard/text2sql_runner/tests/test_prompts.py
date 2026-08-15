from __future__ import annotations

import json
import unittest

from workspace.standard.competition_eval.sql_tools import SqlSafetyError
from workspace.standard.text2sql_runner.competition_data import CompetitionQuestion
from workspace.standard.text2sql_runner.prompts import build_messages, clean_model_sql


class PromptConstructionTests(unittest.TestCase):
    def test_prompt_contains_question_and_schema_without_answer_fields(self) -> None:
        question = CompetitionQuestion(id=1, question="客户数量")

        messages = build_messages(question, "customer(id bigint NOT NULL)")

        rendered = json.dumps(messages, ensure_ascii=False)
        self.assertIn("客户数量", rendered)
        self.assertIn("customer(id bigint NOT NULL)", rendered)
        self.assertNotIn("gold", rendered.lower())
        self.assertNotIn("标准 SQL", rendered)
        self.assertEqual([message["role"] for message in messages], ["system", "user"])


class ModelSqlCleaningTests(unittest.TestCase):
    def test_removes_one_complete_markdown_sql_fence(self) -> None:
        self.assertEqual(
            clean_model_sql("```sql\nSELECT 1;\n```"),
            "SELECT 1;",
        )

    def test_preserves_plain_read_only_sql(self) -> None:
        self.assertEqual(
            clean_model_sql("  WITH value AS (SELECT 1 AS n) SELECT n FROM value;  "),
            "WITH value AS (SELECT 1 AS n) SELECT n FROM value;",
        )

    def test_rejects_text_around_markdown_fence(self) -> None:
        with self.assertRaisesRegex(SqlSafetyError, "只允许返回 SQL"):
            clean_model_sql("答案如下：\n```sql\nSELECT 1\n```")

    def test_rejects_multiple_or_writing_statements(self) -> None:
        invalid_answers = (
            "SELECT 1; SELECT 2;",
            "DELETE FROM customer",
            "SELECT * INTO copied_customer FROM customer",
        )
        for answer in invalid_answers:
            with self.subTest(answer=answer):
                with self.assertRaises(SqlSafetyError):
                    clean_model_sql(answer)

    def test_rejects_empty_content(self) -> None:
        with self.assertRaisesRegex(SqlSafetyError, "SQL 为空"):
            clean_model_sql("  ")


if __name__ == "__main__":
    unittest.main()
