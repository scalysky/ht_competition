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
    / "running-text2sql-no-at2s-benchmark"
    / "scripts"
    / "validate_predictions.py"
)
SEPARATOR = "-" * 40


class NoAt2sPredictionValidatorTests(unittest.TestCase):
    def run_validator(
        self,
        content: str,
        expected_count: int,
        *,
        repo_root: Path = REPO_ROOT,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            predictions = Path(temp_dir) / "predictions.txt"
            predictions.write_text(content, encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    str(predictions),
                    "--expected-count",
                    str(expected_count),
                    "--repo-root",
                    str(repo_root),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )

    def test_accepts_dynamic_count_and_reports_digest(self) -> None:
        content = f"\n{SEPARATOR}\n".join(
            f"SELECT {index}" for index in range(1, 4)
        )

        completed = self.run_validator(content, expected_count=3)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("count=3", completed.stdout)
        self.assertRegex(completed.stdout, r"sha256=[0-9a-f]{64}")

    def test_rejects_markdown_or_unsafe_sql(self) -> None:
        markdown = self.run_validator("```sql\nSELECT 1\n```", expected_count=1)
        unsafe = self.run_validator("DELETE FROM dim_public", expected_count=1)

        self.assertNotEqual(markdown.returncode, 0)
        self.assertIn("Markdown", markdown.stderr)
        self.assertNotEqual(unsafe.returncode, 0)
        self.assertIn("只读安全检查", unsafe.stderr)

    def test_rejects_wrong_count_and_non_repo_root(self) -> None:
        wrong_count = self.run_validator("SELECT 1", expected_count=2)
        wrong_root = self.run_validator(
            "SELECT 1",
            expected_count=1,
            repo_root=REPO_ROOT / "workspace" / "skills",
        )

        self.assertNotEqual(wrong_count.returncode, 0)
        self.assertIn("应为 2 条", wrong_count.stderr)
        self.assertNotEqual(wrong_root.returncode, 0)
        self.assertIn("指定的评测仓库", wrong_root.stderr)


if __name__ == "__main__":
    unittest.main()
