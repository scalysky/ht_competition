from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_DIR))

from evaluate import load_sql_cases  # noqa: E402
from metrics import execution_match, exact_match, rves_reward, rves_score  # noqa: E402
from sql_tools import SqlSafetyError, normalize_sql, validate_read_only_sql  # noqa: E402


class SqlNormalizationTests(unittest.TestCase):
    def test_whitespace_case_comments_and_terminal_semicolon_are_ignored(self) -> None:
        left = "SELECT A.PTY_ID -- comment\nFROM ADS_CUST_INFO_D A;"
        right = " select  a.pty_id from ads_cust_info_d a "
        self.assertTrue(exact_match(left, right))

    def test_string_literal_case_is_preserved(self) -> None:
        self.assertNotEqual(normalize_sql("SELECT 'A'"), normalize_sql("SELECT 'a'"))

    def test_different_predicate_is_not_exact_match(self) -> None:
        self.assertFalse(exact_match("SELECT 1 WHERE 2 > 1", "SELECT 1 WHERE 2 >= 1"))


class SqlSafetyTests(unittest.TestCase):
    def test_select_and_read_only_cte_are_allowed(self) -> None:
        validate_read_only_sql("SELECT * FROM dim_public")
        validate_read_only_sql("WITH x AS (SELECT 1) SELECT * FROM x;")

    def test_dangerous_or_multiple_statements_are_rejected(self) -> None:
        unsafe = (
            "DELETE FROM dim_public",
            "WITH x AS (DELETE FROM dim_public RETURNING *) SELECT * FROM x",
            "SELECT * INTO temp_table FROM dim_public",
            "SELECT 1; SELECT 2",
        )
        for sql in unsafe:
            with self.subTest(sql=sql), self.assertRaises(SqlSafetyError):
                validate_read_only_sql(sql)

    def test_keywords_inside_strings_and_comments_are_not_rejected(self) -> None:
        validate_read_only_sql("SELECT 'DROP TABLE x; -- harmless' /* DELETE */")


class ExecutionMatchTests(unittest.TestCase):
    def test_default_matches_bird_set_semantics(self) -> None:
        gold = [(1,), (2,), (2,)]
        predicted = [(2,), (1,)]
        self.assertTrue(execution_match(predicted, gold))

    def test_column_order_is_preserved(self) -> None:
        self.assertFalse(execution_match([(1, 2)], [(2, 1)]))

    def test_optional_order_and_duplicate_sensitivity(self) -> None:
        self.assertFalse(execution_match([(2,), (1,)], [(1,), (2,)], order_sensitive=True))
        self.assertFalse(
            execution_match([(1,), (2,)], [(1,), (2,), (2,)], duplicate_sensitive=True)
        )


class RvesTests(unittest.TestCase):
    def test_official_reward_bands(self) -> None:
        cases = (
            (0, 0),
            (0.1, 0.25),
            (0.25, 0.5),
            (0.5, 0.75),
            (1, 1),
            (2, 1.25),
        )
        for ratio, reward in cases:
            with self.subTest(ratio=ratio):
                self.assertEqual(rves_reward(ratio), reward)
        self.assertAlmostEqual(rves_score(1.25), 111.80339887498948)


class InputFormatTests(unittest.TestCase):
    def test_list_and_mapping_formats_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            list_path = Path(temp_dir) / "list.json"
            list_path.write_text(
                json.dumps([{"id": 1, "question": "q", "sql": "SELECT 1"}]),
                encoding="utf-8",
            )
            mapping_path = Path(temp_dir) / "mapping.json"
            mapping_path.write_text(json.dumps({"1": "SELECT 1"}), encoding="utf-8")
            self.assertEqual(load_sql_cases(list_path)[0]["id"], "1")
            self.assertEqual(load_sql_cases(mapping_path)[0]["sql"], "SELECT 1")


if __name__ == "__main__":
    unittest.main()

