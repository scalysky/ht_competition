from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys


def _configure_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def _get_evaluator_dir(repo_root: Path) -> Path:
    candidate = repo_root.resolve() / "workspace" / "standard" / "competition_eval"
    if (candidate / "evaluate.py").is_file() and (candidate / "sql_tools.py").is_file():
        return candidate
    raise RuntimeError(
        f"指定的评测仓库缺少 workspace/standard/competition_eval: {repo_root.resolve()}"
    )


def validate_predictions(path: Path, expected_count: int, repo_root: Path) -> tuple[int, str]:
    if not path.is_file():
        raise ValueError(f"预测文件不存在: {path}")

    text = path.read_text(encoding="utf-8-sig")
    if "```" in text:
        raise ValueError("predictions.txt 不得包含 Markdown 代码围栏")

    evaluator_dir = _get_evaluator_dir(repo_root)
    sys.path.insert(0, str(evaluator_dir))
    from evaluate import load_sql_cases  # type: ignore[import-not-found]
    from sql_tools import SqlSafetyError, validate_read_only_sql  # type: ignore[import-not-found]

    cases = load_sql_cases(path.resolve())
    if len(cases) != expected_count:
        raise ValueError(f"SQL 数量应为 {expected_count} 条，实际为 {len(cases)} 条")

    for index, case in enumerate(cases, start=1):
        try:
            validate_read_only_sql(case["sql"])
        except SqlSafetyError as exc:
            raise ValueError(f"第 {index} 条 SQL 未通过只读安全检查: {exc}") from exc

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return len(cases), digest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and freeze benchmark predictions")
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--expected-count", type=int, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    return parser.parse_args()


def main() -> int:
    _configure_utf8()
    args = parse_args()
    try:
        count, digest = validate_predictions(
            args.predictions,
            expected_count=args.expected_count,
            repo_root=args.repo_root,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"validation_error: {exc}", file=sys.stderr)
        return 1

    print(f"validation_ok count={count} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
