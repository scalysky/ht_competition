from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = (
    REPO_ROOT
    / "workspace"
    / "skills"
    / "running-text2sql-benchmark"
    / "scripts"
    / "validate_predictions.py"
)
SEPARATOR = "-" * 40


class BenchmarkPredictionValidatorTests(unittest.TestCase):
    def run_validator(
        self,
        content: str,
        expected_count: int | None,
        *,
        repo_root: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            predictions = Path(temp_dir) / "predictions.txt"
            predictions.write_text(content, encoding="utf-8")
            command = [sys.executable, str(VALIDATOR), str(predictions)]
            if expected_count is not None:
                command.extend(["--expected-count", str(expected_count)])
            if repo_root is not None:
                command.extend(["--repo-root", str(repo_root)])
            return subprocess.run(
                command,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )

    def test_accepts_dynamic_query_count_and_reports_digest(self) -> None:
        content = f"\n{SEPARATOR}\n".join(f"SELECT {index}" for index in range(1, 4))

        completed = self.run_validator(content, expected_count=3)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("count=3", completed.stdout)
        self.assertRegex(completed.stdout, r"sha256=[0-9a-f]{64}")

    def test_rejects_markdown_fences_before_evaluation(self) -> None:
        queries = ["```sql\nSELECT 1\n```"] + [f"SELECT {index}" for index in range(2, 8)]

        completed = self.run_validator(
            f"\n{SEPARATOR}\n".join(queries), expected_count=7
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Markdown", completed.stderr)

    def test_rejects_unsafe_sql_before_evaluation(self) -> None:
        queries = ["DELETE FROM dim_public"] + [f"SELECT {index}" for index in range(2, 8)]

        completed = self.run_validator(
            f"\n{SEPARATOR}\n".join(queries), expected_count=7
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("第 1 条 SQL", completed.stderr)

    def test_rejects_wrong_query_count(self) -> None:
        content = f"\n{SEPARATOR}\n".join(f"SELECT {index}" for index in range(1, 7))

        completed = self.run_validator(content, expected_count=7)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("应为 7 条", completed.stderr)

    def test_requires_expected_count_instead_of_assuming_seven(self) -> None:
        content = f"\n{SEPARATOR}\n".join(f"SELECT {index}" for index in range(1, 8))

        completed = self.run_validator(content, expected_count=None)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--expected-count", completed.stderr)

    def test_repo_root_is_exact_and_does_not_search_parent_directories(self) -> None:
        completed = self.run_validator(
            "SELECT 1\n",
            expected_count=1,
            repo_root=REPO_ROOT / "workspace" / "skills",
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("指定的评测仓库", completed.stderr)


if __name__ == "__main__":
    unittest.main()
