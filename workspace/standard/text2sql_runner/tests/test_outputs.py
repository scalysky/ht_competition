from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from workspace.standard.text2sql_runner.competition_data import CompetitionQuestion
from workspace.standard.text2sql_runner.outputs import (
    PredictionRecord,
    append_checkpoint,
    input_fingerprint,
    load_successful_checkpoints,
    write_run_metadata,
    write_prediction_files,
)


class OutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.gold_path = self.root / "gold.json"
        self.gold_path.write_text(
            json.dumps(
                [
                    {"id": 1, "question": "问题一", "sql": "SELECT 1"},
                    {"id": 2, "question": "问题二", "sql": "SELECT 2"},
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_text_output_uses_exact_separator_without_trailing_separator(self) -> None:
        records = [
            PredictionRecord(1, "SELECT 1", "fp-1", "success", None),
            PredictionRecord(2, "SELECT 2", "fp-2", "success", None),
        ]

        paths = write_prediction_files(self.root, records, self.gold_path, [1, 2])

        self.assertEqual(
            paths.text.read_text(encoding="utf-8"),
            "SELECT 1\n----------------------------------------\nSELECT 2\n",
        )
        predictions = json.loads(paths.predictions.read_text(encoding="utf-8"))
        self.assertEqual(
            predictions,
            [{"id": 1, "sql": "SELECT 1"}, {"id": 2, "sql": "SELECT 2"}],
        )

    def test_checkpoint_resume_requires_matching_fingerprint(self) -> None:
        checkpoint = self.root / "checkpoint.jsonl"
        append_checkpoint(
            checkpoint,
            PredictionRecord(1, "SELECT 1", "old", "success", None),
        )
        append_checkpoint(
            checkpoint,
            PredictionRecord(2, None, "fp-2", "error", "timeout"),
        )

        loaded = load_successful_checkpoints(checkpoint)

        self.assertIn((1, "old"), loaded)
        self.assertNotIn((1, "new"), loaded)
        self.assertNotIn((2, "fp-2"), loaded)

    def test_malformed_checkpoint_reports_line_number(self) -> None:
        checkpoint = self.root / "checkpoint.jsonl"
        checkpoint.write_text(
            '{"id":1,"sql":"SELECT 1","fingerprint":"fp-1",'
            '"status":"success","error":null}\nnot-json\n',
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "第 2 行"):
            load_successful_checkpoints(checkpoint)

    def test_gold_subset_and_errors_follow_selected_ids(self) -> None:
        records = [
            PredictionRecord(2, None, "fp-2", "error", "request failed"),
        ]

        paths = write_prediction_files(self.root, records, self.gold_path, [2])

        gold = json.loads(paths.gold.read_text(encoding="utf-8"))
        errors = json.loads(paths.errors.read_text(encoding="utf-8"))
        self.assertEqual([item["id"] for item in gold], [2])
        self.assertEqual(errors, [{"id": 2, "error": "request failed"}])
        self.assertEqual(paths.text.read_text(encoding="utf-8"), "")

    def test_fingerprint_changes_when_model_or_question_changes(self) -> None:
        question = CompetitionQuestion(1, "客户数量")
        messages = [{"role": "user", "content": "客户数量"}]

        first = input_fingerprint(question, "schema", "model-a", messages)
        second = input_fingerprint(question, "schema", "model-b", messages)
        changed_question = input_fingerprint(
            CompetitionQuestion(1, "客户总数"), "schema", "model-a", messages
        )

        self.assertEqual(len(first), 64)
        self.assertNotEqual(first, second)
        self.assertNotEqual(first, changed_question)

    def test_fingerprint_separates_full_and_none_knowledge_contexts(self) -> None:
        question = CompetitionQuestion(1, "客户数量")
        none_context = "TABLE customer(id)"
        full_context = none_context + "\n\n知识：客户主键是 id"
        none_messages = [{"role": "user", "content": none_context}]
        full_messages = [{"role": "user", "content": full_context}]

        none_fingerprint = input_fingerprint(
            question, none_context, "model-a", none_messages
        )
        full_fingerprint = input_fingerprint(
            question, full_context, "model-a", full_messages
        )

        self.assertNotEqual(none_fingerprint, full_fingerprint)

    def test_run_metadata_records_mode_files_and_model_without_secrets(self) -> None:
        path = write_run_metadata(
            self.root,
            knowledge_mode="Full",
            knowledge_files=("architecture/a.md", "architecture/b.md"),
            model="deepseek-v4-flash",
        )

        metadata = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            set(metadata),
            {"generated_at", "knowledge_mode", "knowledge_files", "model"},
        )
        self.assertEqual(metadata["knowledge_mode"], "Full")
        self.assertEqual(
            metadata["knowledge_files"],
            ["architecture/a.md", "architecture/b.md"],
        )
        self.assertEqual(metadata["model"], "deepseek-v4-flash")
        self.assertRegex(metadata["generated_at"], r"^\d{4}-\d{2}-\d{2}T")


if __name__ == "__main__":
    unittest.main()
