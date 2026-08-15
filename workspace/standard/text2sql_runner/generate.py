from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Protocol, Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
COMPETITION_EVAL_DIR = REPO_ROOT / "workspace" / "standard" / "competition_eval"
if str(COMPETITION_EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(COMPETITION_EVAL_DIR))

from db_config import DatabaseConfig, load_env_file  # noqa: E402
from psql_runner import PsqlRunner  # noqa: E402

from workspace.standard.text2sql_runner.competition_data import (  # noqa: E402
    CompetitionQuestion,
    format_schema,
    load_questions,
)
from workspace.standard.text2sql_runner.llm_client import (  # noqa: E402
    LlmConfig,
    OpenAICompatibleClient,
)
from workspace.standard.text2sql_runner.knowledge import (  # noqa: E402
    KNOWLEDGE_MODES,
    combine_schema_and_knowledge,
    load_knowledge_context,
)
from workspace.standard.text2sql_runner.outputs import (  # noqa: E402
    OutputPaths,
    PredictionRecord,
    append_checkpoint,
    input_fingerprint,
    load_successful_checkpoints,
    write_prediction_files,
    write_run_metadata,
)
from workspace.standard.text2sql_runner.prompts import (  # noqa: E402
    build_messages,
    clean_model_sql,
)


DEFAULT_GOLD = COMPETITION_EVAL_DIR / "gold_queries.json"
DEFAULT_KNOWLEDGE_ROOT = (
    REPO_ROOT
    / "workspace"
    / "skills"
    / "at2s"
    / ".knowledge"
)


class ModelClient(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str: ...


@dataclass(frozen=True)
class GenerationSummary:
    total: int
    successful: int
    failed: int
    resumed: int
    outputs: OutputPaths


def select_questions(
    questions: Sequence[CompetitionQuestion],
    *,
    limit: int | None,
    full: bool,
) -> list[CompetitionQuestion]:
    if full == (limit is not None):
        raise ValueError("必须且只能选择 --limit N 或 --full")
    if full:
        return list(questions)
    if limit is None or limit <= 0:
        raise ValueError("--limit 必须大于 0")
    if limit > len(questions):
        raise ValueError(f"--limit 不能超过题目总数 {len(questions)}")
    return list(questions[:limit])


def run_generation(
    *,
    questions: Sequence[CompetitionQuestion],
    schema: str,
    model_name: str,
    client: ModelClient,
    output_dir: Path,
    gold_path: Path,
    resume: bool,
) -> GenerationSummary:
    checkpoint_path = output_dir / "checkpoint.jsonl"
    completed = (
        load_successful_checkpoints(checkpoint_path) if resume else {}
    )
    records: list[PredictionRecord] = []
    resumed_count = 0

    for question in questions:
        messages = build_messages(question, schema)
        fingerprint = input_fingerprint(
            question,
            schema,
            model_name,
            messages,
        )
        cached = completed.get((question.id, fingerprint))
        if cached is not None:
            records.append(cached)
            resumed_count += 1
            continue

        try:
            model_content = client.complete(messages)
            sql = clean_model_sql(model_content)
            record = PredictionRecord(
                id=question.id,
                sql=sql,
                fingerprint=fingerprint,
                status="success",
                error=None,
            )
        except Exception as exc:
            detail = str(exc).strip() or type(exc).__name__
            record = PredictionRecord(
                id=question.id,
                sql=None,
                fingerprint=fingerprint,
                status="error",
                error=f"{type(exc).__name__}: {detail}"[:2000],
            )
        append_checkpoint(checkpoint_path, record)
        records.append(record)

    outputs = write_prediction_files(
        output_dir,
        records,
        gold_path,
        [question.id for question in questions],
    )
    successful = sum(record.status == "success" for record in records)
    failed = len(records) - successful
    return GenerationSummary(
        total=len(records),
        successful=successful,
        failed=failed,
        resumed=resumed_count,
        outputs=outputs,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="比赛 PostgreSQL SQL 批量生成器")
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--limit", type=int)
    scope.add_argument("--full", action="store_true")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    parser.add_argument(
        "--knowledge-mode",
        choices=KNOWLEDGE_MODES,
        default="Full",
    )
    parser.add_argument(
        "--knowledge-root",
        type=Path,
        default=DEFAULT_KNOWLEDGE_ROOT,
    )
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--psql-path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    load_env_file()
    llm_config = LlmConfig.from_env()
    questions = select_questions(
        load_questions(args.gold.resolve()),
        limit=args.limit,
        full=args.full,
    )

    database_config = DatabaseConfig.from_env()
    runner = PsqlRunner(database_config, psql_path=args.psql_path)
    identity = runner.check_identity()
    if identity["read_only"] != "on":
        raise RuntimeError("数据库连接不是只读模式，已终止生成")
    schema = format_schema(runner.public_schema_metadata())
    knowledge_context = load_knowledge_context(
        args.knowledge_mode,
        args.knowledge_root.resolve(),
    )
    if knowledge_context.mode == "Full":
        print(f"知识库模式: Full（已加载 {len(knowledge_context.files)} 个文件）")
        for relative_path in knowledge_context.files:
            print(f"  - {relative_path}")
    else:
        print("知识库模式: None（未使用知识库）")
    prompt_context = combine_schema_and_knowledge(schema, knowledge_context)
    write_run_metadata(
        args.output_dir.resolve(),
        knowledge_mode=knowledge_context.mode,
        knowledge_files=knowledge_context.files,
        model=llm_config.model,
    )

    summary = run_generation(
        questions=questions,
        schema=prompt_context,
        model_name=llm_config.model,
        client=OpenAICompatibleClient(llm_config),
        output_dir=args.output_dir.resolve(),
        gold_path=args.gold.resolve(),
        resume=not args.no_resume,
    )
    print(
        f"生成完成: total={summary.total} success={summary.successful} "
        f"failed={summary.failed} resumed={summary.resumed}"
    )
    print(f"Predictions: {summary.outputs.predictions}")
    print(f"Text: {summary.outputs.text}")
    return 2 if summary.failed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
