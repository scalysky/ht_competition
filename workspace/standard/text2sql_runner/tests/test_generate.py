from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from workspace.standard.text2sql_runner.competition_data import CompetitionQuestion
from workspace.standard.text2sql_runner.generate import (
    parse_args,
    run_generation,
    select_questions,
)


class _SequenceClient:
    def __init__(self, responses: list[object], checkpoint: Path | None = None):
        self.responses = list(responses)
        self.checkpoint = checkpoint
        self.messages: list[list[dict[str, str]]] = []

    def complete(self, messages: list[dict[str, str]]) -> str:
        if self.messages and self.checkpoint is not None:
            checkpoint_lines = self.checkpoint.read_text(encoding="utf-8").splitlines()
            if len(checkpoint_lines) < len(self.messages):
                raise AssertionError("上一题未在下一次请求前写入检查点")
        self.messages.append(messages)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        if not isinstance(response, str):
            raise AssertionError("测试响应必须是字符串或异常")
        return response


class GenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.output_dir = self.root / "run"
        self.gold_path = self.root / "gold.json"
        self.gold_path.write_text(
            json.dumps(
                [
                    {"id": 1, "question": "问题一", "sql": "SECRET_GOLD_SQL_1"},
                    {"id": 2, "question": "问题二", "sql": "SECRET_GOLD_SQL_2"},
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.questions = [
            CompetitionQuestion(1, "问题一"),
            CompetitionQuestion(2, "问题二"),
        ]

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_generation_checkpoints_before_next_request_and_hides_gold(self) -> None:
        checkpoint = self.output_dir / "checkpoint.jsonl"
        client = _SequenceClient(["SELECT 1", "SELECT 2"], checkpoint)

        summary = run_generation(
            questions=self.questions,
            schema="customer(id bigint)",
            model_name="model-a",
            client=client,
            output_dir=self.output_dir,
            gold_path=self.gold_path,
            resume=True,
        )

        self.assertEqual((summary.successful, summary.failed, summary.resumed), (2, 0, 0))
        self.assertEqual(len(checkpoint.read_text(encoding="utf-8").splitlines()), 2)
        rendered_messages = json.dumps(client.messages, ensure_ascii=False)
        self.assertNotIn("SECRET_GOLD_SQL", rendered_messages)

    def test_generation_continues_after_one_model_failure(self) -> None:
        client = _SequenceClient([RuntimeError("temporary failure"), "SELECT 2"])

        summary = run_generation(
            questions=self.questions,
            schema="customer(id bigint)",
            model_name="model-a",
            client=client,
            output_dir=self.output_dir,
            gold_path=self.gold_path,
            resume=True,
        )

        self.assertEqual((summary.successful, summary.failed), (1, 1))
        predictions = json.loads(
            (self.output_dir / "predictions.json").read_text(encoding="utf-8")
        )
        self.assertEqual(predictions, [{"id": 2, "sql": "SELECT 2"}])

    def test_generation_resumes_matching_success_without_calling_model(self) -> None:
        first_client = _SequenceClient(["SELECT 1", "SELECT 2"])
        run_generation(
            questions=self.questions,
            schema="customer(id bigint)",
            model_name="model-a",
            client=first_client,
            output_dir=self.output_dir,
            gold_path=self.gold_path,
            resume=True,
        )
        second_client = _SequenceClient([])

        summary = run_generation(
            questions=self.questions,
            schema="customer(id bigint)",
            model_name="model-a",
            client=second_client,
            output_dir=self.output_dir,
            gold_path=self.gold_path,
            resume=True,
        )

        self.assertEqual((summary.successful, summary.resumed), (2, 2))
        self.assertEqual(second_client.messages, [])

    def test_select_questions_requires_explicit_valid_scope(self) -> None:
        self.assertEqual(
            select_questions(self.questions, limit=1, full=False),
            [CompetitionQuestion(1, "问题一")],
        )
        self.assertEqual(
            select_questions(self.questions, limit=None, full=True),
            self.questions,
        )
        invalid_scopes = ((None, False), (1, True), (0, False), (3, False))
        for limit, full in invalid_scopes:
            with self.subTest(limit=limit, full=full):
                with self.assertRaises(ValueError):
                    select_questions(self.questions, limit=limit, full=full)

    def test_cli_defaults_to_full_knowledge_and_accepts_none(self) -> None:
        default_args = parse_args(
            ["--limit", "1", "--output-dir", str(self.output_dir)]
        )
        none_args = parse_args(
            [
                "--limit",
                "1",
                "--output-dir",
                str(self.output_dir),
                "--knowledge-mode",
                "None",
            ]
        )

        self.assertEqual(default_args.knowledge_mode, "Full")
        self.assertEqual(none_args.knowledge_mode, "None")


if __name__ == "__main__":
    unittest.main()
