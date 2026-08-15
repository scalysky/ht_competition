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
        self.assertIn("-Limit", completed.stdout)
        self.assertIn("-Full", completed.stdout)
        self.assertIn("-GenerateOnly", completed.stdout)

    def test_limit_and_full_are_mutually_exclusive(self) -> None:
        completed = self.run_launcher("-Limit", "1", "-Full")
        self.assertNotEqual(completed.returncode, 0)

    def test_partial_generation_still_evaluates_and_returns_two(self) -> None:
        run_name = "launcher-partial-test"
        with tempfile.TemporaryDirectory() as output_root:
            run_dir = Path(output_root) / run_name
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "predictions.json").write_text("[]\n", encoding="utf-8")
            (run_dir / "gold_subset.json").write_text("[]\n", encoding="utf-8")
            with tempfile.TemporaryDirectory() as command_dir:
                fake_python = Path(command_dir) / "python.cmd"
                fake_python.write_text(
                    "@echo off\n"
                    "echo %* | findstr /C:\"workspace.standard.text2sql_runner.generate\" >nul\n"
                    "if %errorlevel%==0 exit /b 2\n"
                    "exit /b 0\n",
                    encoding="ascii",
                )
                environment = os.environ.copy()
                environment["PATH"] = command_dir + os.pathsep + environment["PATH"]

                completed = self.run_launcher(
                    "-Limit",
                    "1",
                    "-RunName",
                    run_name,
                    "-OutputRoot",
                    output_root,
                    environment=environment,
                )

            self.assertEqual(completed.returncode, 2, completed.stdout)
            self.assertIn("Run output:", completed.stdout)


if __name__ == "__main__":
    unittest.main()
