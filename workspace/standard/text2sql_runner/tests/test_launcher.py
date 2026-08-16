from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[4]
LAUNCHER = REPO_ROOT / "run_text2sql.ps1"


@unittest.skipUnless(shutil.which("powershell"), "需要 Windows PowerShell")
class PowerShellLauncherTests(unittest.TestCase):
    def run_launcher(
        self,
        *arguments: str,
        environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(LAUNCHER),
                *arguments,
            ],
            cwd=REPO_ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20,
            check=False,
            env=environment,
        )

    def test_help_succeeds_without_loading_credentials(self) -> None:
        completed = self.run_launcher("-Help")
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("-Predictions", completed.stdout)
        self.assertIn("JSON", completed.stdout)
        self.assertIn("TXT", completed.stdout)

    def test_predictions_is_required(self) -> None:
        completed = self.run_launcher("-RunName", "missing-input")
        self.assertNotEqual(completed.returncode, 0)

    def test_json_input_is_forwarded_to_fixed_three_metric_evaluator(self) -> None:
        run_name = "launcher-json-test"
        with tempfile.TemporaryDirectory() as output_root:
            predictions = Path(output_root) / "answers.json"
            predictions.write_text('[{"id": 1, "sql": "SELECT 1"}]\n', encoding="utf-8")
            with tempfile.TemporaryDirectory() as command_dir:
                fake_python = Path(command_dir) / "python.cmd"
                fake_python.write_text(
                    "@echo off\necho %*\nexit /b 0\n",
                    encoding="ascii",
                )
                environment = os.environ.copy()
                environment["PATH"] = command_dir + os.pathsep + environment["PATH"]

                completed = self.run_launcher(
                    "-Predictions",
                    str(predictions),
                    "-RunName",
                    run_name,
                    "-OutputRoot",
                    output_root,
                    environment=environment,
                )

            self.assertEqual(completed.returncode, 0, completed.stdout)
            self.assertIn("Input format: JSON", completed.stdout)
            self.assertIn("--metrics em,ex,rves", completed.stdout)
            self.assertIn("--predictions", completed.stdout)
            self.assertNotIn("text2sql_runner.generate", completed.stdout)

    def test_txt_input_is_detected_case_insensitively(self) -> None:
        with tempfile.TemporaryDirectory() as output_root:
            predictions = Path(output_root) / "answers.TXT"
            predictions.write_text("SELECT 1\n", encoding="utf-8")
            with tempfile.TemporaryDirectory() as command_dir:
                fake_python = Path(command_dir) / "python.cmd"
                fake_python.write_text("@echo off\necho %*\nexit /b 0\n", encoding="ascii")
                environment = os.environ.copy()
                environment["PATH"] = command_dir + os.pathsep + environment["PATH"]

                completed = self.run_launcher(
                    "-Predictions",
                    str(predictions),
                    "-OutputRoot",
                    output_root,
                    environment=environment,
                )

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("Input format: TXT", completed.stdout)


if __name__ == "__main__":
    unittest.main()
