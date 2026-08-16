from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
import json
import re
from statistics import fmean
import sys
from typing import Any

from db_config import DatabaseConfig
from metrics import (
    clean_abnormal_ratios,
    exact_match,
    execution_match,
    rves_reward,
    rves_score,
)
from psql_runner import PsqlExecutionError, PsqlRunner
from sql_tools import SqlSafetyError, validate_read_only_sql


DEFAULT_GOLD = Path(__file__).with_name("gold_queries.json")
DEFAULT_OUTPUT = Path(__file__).parents[1] / "eval_runs" / "competition_evaluation.json"
SUPPORTED_METRICS = {"em", "ex", "rves"}
TXT_SEPARATOR = re.compile(r"(?m)^[ \t]*-{40}[ \t]*\r?$")


def _case_id(value: Any) -> str:
    if value is None or str(value).strip() == "":
        raise ValueError("评测样本缺少 id")
    return str(value).strip()


def detect_input_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return "json"
    if suffix == ".txt":
        return "txt"
    raise ValueError(f"{path} 格式不支持，仅支持 .json 或 .txt")


def _load_txt_cases(path: Path) -> list[dict[str, Any]]:
    content = path.read_text(encoding="utf-8-sig")
    if not content.strip():
        raise ValueError(f"{path} 为空，没有可评测的 SQL")

    sql_answers = TXT_SEPARATOR.split(content)
    cases: list[dict[str, Any]] = []
    for index, answer in enumerate(sql_answers, start=1):
        sql = answer.strip()
        if not sql:
            raise ValueError(f"{path} 第 {index} 个 SQL 为空，请检查 40 个横线分隔符")
        cases.append({"id": str(index), "sql": sql})
    return cases


def load_sql_cases(path: Path) -> list[dict[str, Any]]:
    input_format = detect_input_format(path)
    if input_format == "txt":
        return _load_txt_cases(path)

    data = json.loads(path.read_text(encoding="utf-8-sig"))
    cases: list[dict[str, Any]] = []
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                raise ValueError(f"{path} 中的样本必须是 JSON 对象")
            case = dict(item)
            case["id"] = _case_id(case.get("id"))
            if not isinstance(case.get("sql"), str):
                raise ValueError(f"{path} 样本 {case['id']} 缺少 SQL 字符串")
            cases.append(case)
    elif isinstance(data, dict):
        for raw_id, value in data.items():
            if isinstance(value, str):
                cases.append({"id": _case_id(raw_id), "sql": value})
            elif isinstance(value, dict) and isinstance(value.get("sql"), str):
                case = dict(value)
                case["id"] = _case_id(raw_id)
                cases.append(case)
            else:
                raise ValueError(f"{path} 样本 {raw_id} 缺少 SQL 字符串")
    else:
        raise ValueError(f"{path} 顶层必须是 JSON 数组或对象")

    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path} 包含重复 id")
    return cases


def _measure_rves(
    runner: PsqlRunner,
    predicted_sql: str,
    gold_sql: str,
    *,
    iterations: int,
    warmups: int,
) -> dict[str, Any]:
    for _ in range(warmups):
        runner.execution_time_ms(gold_sql)
        runner.execution_time_ms(predicted_sql)

    ratios: list[float] = []
    gold_times: list[float] = []
    predicted_times: list[float] = []
    for index in range(iterations):
        if index % 2 == 0:
            gold_ms = runner.execution_time_ms(gold_sql)
            predicted_ms = runner.execution_time_ms(predicted_sql)
        else:
            predicted_ms = runner.execution_time_ms(predicted_sql)
            gold_ms = runner.execution_time_ms(gold_sql)
        gold_times.append(gold_ms)
        predicted_times.append(predicted_ms)
        ratios.append(gold_ms / max(predicted_ms, 1e-9))

    cleaned = clean_abnormal_ratios(ratios)
    time_ratio = fmean(cleaned) if cleaned else 0.0
    reward = rves_reward(time_ratio)
    return {
        "time_ratio": round(time_ratio, 6),
        "reward": reward,
        "score": round(rves_score(reward), 4),
        "gold_mean_ms": round(fmean(gold_times), 4),
        "predicted_mean_ms": round(fmean(predicted_times), 4),
        "ratios": [round(value, 6) for value in ratios],
    }


def evaluate_cases(
    gold_cases: list[dict[str, Any]],
    prediction_cases: list[dict[str, Any]],
    *,
    metrics: set[str],
    runner: PsqlRunner | None,
    ves_iterations: int,
    ves_warmups: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    predictions = {case["id"]: case for case in prediction_cases}
    gold_ids = {case["id"] for case in gold_cases}
    extra_prediction_ids = sorted(set(predictions) - gold_ids)
    results: list[dict[str, Any]] = []

    for gold in gold_cases:
        case_id = gold["id"]
        prediction = predictions.get(case_id)
        predicted_sql = prediction["sql"] if prediction else ""
        errors: list[dict[str, str]] = []
        result: dict[str, Any] = {
            "id": case_id,
            "question": gold.get("question", ""),
            "gold_sql": gold["sql"],
            "predicted_sql": predicted_sql,
            "prediction_present": prediction is not None,
            "em": 0,
            "ex": 0,
            "rves": {
                "time_ratio": 0.0,
                "reward": 0.0,
                "score": 0.0,
                "gold_mean_ms": None,
                "predicted_mean_ms": None,
                "ratios": [],
            },
            "gold_row_count": None,
            "predicted_row_count": None,
            "empty_result_match": False,
            "errors": errors,
        }

        try:
            validate_read_only_sql(gold["sql"])
        except SqlSafetyError as exc:
            raise RuntimeError(f"标准 SQL #{case_id} 未通过安全校验: {exc}") from exc

        if "em" in metrics:
            try:
                result["em"] = int(exact_match(predicted_sql, gold["sql"]))
            except SqlSafetyError as exc:
                errors.append({"stage": "em", "category": "parse_error", "message": str(exc)})

        predicted_safe = True
        try:
            validate_read_only_sql(predicted_sql)
        except SqlSafetyError as exc:
            predicted_safe = False
            errors.append({"stage": "safety", "category": "unsafe_sql", "message": str(exc)})

        needs_execution = "ex" in metrics or "rves" in metrics
        if needs_execution:
            if runner is None:
                raise RuntimeError("EX/R-VES 需要 PostgreSQL 连接")
            try:
                gold_rows = runner.execute_rows(gold["sql"])
            except (PsqlExecutionError, SqlSafetyError) as exc:
                category = getattr(exc, "category", "gold_execution_error")
                raise RuntimeError(f"标准 SQL #{case_id} 执行失败 [{category}]: {exc}") from exc

            result["gold_row_count"] = gold_rows.row_count
            predicted_rows = None
            if predicted_safe:
                try:
                    predicted_rows = runner.execute_rows(predicted_sql)
                    result["predicted_row_count"] = predicted_rows.row_count
                except PsqlExecutionError as exc:
                    errors.append(
                        {
                            "stage": "execution",
                            "category": exc.category,
                            "message": str(exc),
                        }
                    )

            if predicted_rows is not None:
                order_sensitive = bool(gold.get("order_sensitive", False))
                duplicate_sensitive = bool(gold.get("duplicate_sensitive", False))
                result["ex"] = int(
                    execution_match(
                        predicted_rows.rows,
                        gold_rows.rows,
                        order_sensitive=order_sensitive,
                        duplicate_sensitive=duplicate_sensitive,
                    )
                )
                result["empty_result_match"] = bool(
                    result["ex"] and gold_rows.row_count == 0 and predicted_rows.row_count == 0
                )

        if "rves" in metrics and result["ex"]:
            try:
                result["rves"] = _measure_rves(
                    runner,
                    predicted_sql,
                    gold["sql"],
                    iterations=ves_iterations,
                    warmups=ves_warmups,
                )
            except PsqlExecutionError as exc:
                errors.append(
                    {
                        "stage": "rves",
                        "category": exc.category,
                        "message": str(exc),
                    }
                )

        results.append(result)
        em_display = result["em"] if "em" in metrics else "N/A"
        ex_display = result["ex"] if "ex" in metrics or "rves" in metrics else "N/A"
        rves_display = f"{result['rves']['score']:.2f}" if "rves" in metrics else "N/A"
        print(
            f"#{case_id}: EM={em_display} EX={ex_display} "
            f"R-VES={rves_display} rows={result['predicted_row_count']}"
        )

    total = len(results)
    summary = {
        "total": total,
        "em_correct": sum(item["em"] for item in results),
        "em": (
            round(sum(item["em"] for item in results) / total * 100, 4)
            if total and "em" in metrics
            else None
        ),
        "ex_correct": sum(item["ex"] for item in results),
        "ex": (
            round(sum(item["ex"] for item in results) / total * 100, 4)
            if total and ("ex" in metrics or "rves" in metrics)
            else None
        ),
        "rves": (
            round(fmean(item["rves"]["score"] for item in results), 4)
            if total and "rves" in metrics
            else None
        ),
        "empty_result_matches": sum(item["empty_result_match"] for item in results),
        "prediction_errors": sum(bool(item["errors"]) for item in results),
        "missing_prediction_ids": [
            item["id"] for item in results if not item["prediction_present"]
        ],
        "extra_prediction_ids": extra_prediction_ids,
    }
    return results, summary


def write_reports(
    output_path: Path,
    *,
    metadata: dict[str, Any],
    summary: dict[str, Any],
    results: list[dict[str, Any]],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"metadata": metadata, "summary": summary, "cases": results}
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_path = output_path.with_suffix(".csv")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=(
                "id",
                "question",
                "em",
                "ex",
                "rves_score",
                "time_ratio",
                "gold_row_count",
                "predicted_row_count",
                "empty_result_match",
                "errors",
            ),
        )
        writer.writeheader()
        for item in results:
            writer.writerow(
                {
                    "id": item["id"],
                    "question": item["question"],
                    "em": item["em"],
                    "ex": item["ex"],
                    "rves_score": item["rves"]["score"],
                    "time_ratio": item["rves"]["time_ratio"],
                    "gold_row_count": item["gold_row_count"],
                    "predicted_row_count": item["predicted_row_count"],
                    "empty_result_match": item["empty_result_match"],
                    "errors": json.dumps(item["errors"], ensure_ascii=False),
                }
            )

    markdown_path = output_path.with_suffix(".md")
    def score_text(value: float | None) -> str:
        return "N/A" if value is None else f"{value:.2f}"

    lines = [
        "# 比赛 SQL 评测报告",
        "",
        f"- 样本数：{summary['total']}",
        f"- EM：{score_text(summary['em'])}",
        f"- EX：{score_text(summary['ex'])}",
        f"- R-VES：{score_text(summary['rves'])}",
        f"- 空结果匹配：{summary['empty_result_matches']}",
        f"- 预测错误数：{summary['prediction_errors']}",
        "",
        "| ID | EM | EX | R-VES | 标准行数 | 预测行数 | 空结果 |",
        "|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for item in results:
        lines.append(
            f"| {item['id']} | {item['em']} | {item['ex']} | "
            f"{item['rves']['score']:.2f} | {item['gold_row_count']} | "
            f"{item['predicted_row_count']} | {'是' if item['empty_result_match'] else '否'} |"
        )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="比赛 PostgreSQL Text-to-SQL 统一评分器")
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--metrics", default="em,ex,rves")
    parser.add_argument("--ves-iterations", type=int, default=5)
    parser.add_argument("--ves-warmups", type=int, default=1)
    parser.add_argument("--psql-path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    metrics = {item.strip().lower() for item in args.metrics.split(",") if item.strip()}
    unsupported = metrics - SUPPORTED_METRICS
    if not metrics or unsupported:
        raise ValueError(f"不支持的指标: {', '.join(sorted(unsupported))}")
    if args.ves_iterations < 1 or args.ves_warmups < 0:
        raise ValueError("R-VES 重复次数必须大于 0，预热次数不能为负数")

    gold_cases = load_sql_cases(args.gold.resolve())
    predictions_path = args.predictions.resolve()
    prediction_format = detect_input_format(predictions_path)
    prediction_cases = load_sql_cases(predictions_path)
    print(f"输入格式: {prediction_format.upper()}（{len(prediction_cases)} 条 SQL）")
    runner = None
    identity = None
    if metrics & {"ex", "rves"}:
        config = DatabaseConfig.from_env()
        runner = PsqlRunner(config, psql_path=args.psql_path)
        identity = runner.check_identity()
        if identity["read_only"] != "on":
            raise RuntimeError("数据库连接不是只读模式，已终止评测")
        print(
            f"PostgreSQL: user={identity['user']} database={identity['database']} "
            f"read_only={identity['read_only']} timeout={identity['statement_timeout']}"
        )

    results, summary = evaluate_cases(
        gold_cases,
        prediction_cases,
        metrics=metrics,
        runner=runner,
        ves_iterations=args.ves_iterations,
        ves_warmups=args.ves_warmups,
    )
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dialect": "PostgreSQL",
        "metrics": sorted(metrics),
        "gold_path": str(args.gold.resolve()),
        "predictions_path": str(predictions_path),
        "predictions_format": prediction_format,
        "result_comparison": {
            "row_order": "ignored_by_default",
            "duplicates": "ignored_by_default",
            "column_order": "preserved",
        },
        "rves": {
            "iterations": args.ves_iterations,
            "warmups": args.ves_warmups,
            "timing_source": "PostgreSQL EXPLAIN ANALYZE Execution Time",
            "identity": identity,
        },
    }
    write_reports(args.output.resolve(), metadata=metadata, summary=summary, results=results)
    def display(value: float | None) -> str:
        return "N/A" if value is None else f"{value:.2f}"

    print(
        f"\nSummary: EM={display(summary['em'])} EX={display(summary['ex'])} "
        f"R-VES={display(summary['rves'])}"
    )
    print(f"Report: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
