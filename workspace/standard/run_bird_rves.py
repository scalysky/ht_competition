"""Run the official BIRD Mini-Dev R-VES scorer reproducibly.

The upstream command hard-codes 100 timing iterations.  BIRD's Mini-Dev
README recommends five iterations for a stable R-VES run, so this wrapper
keeps the official SQL execution and scoring functions while exposing the
iteration count and producing machine-readable results.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import sys
import time


STANDARD_DIR = Path(__file__).resolve().parent
EVALUATION_DIR = STANDARD_DIR / "bird_mini_dev_eval" / "evaluation"
if str(EVALUATION_DIR) not in sys.path:
    sys.path.insert(0, str(EVALUATION_DIR))

import evaluation_ves as official_ves  # noqa: E402


DEFAULT_DATASET_DIR = (
    STANDARD_DIR.parent
    / "dataset"
    / "bird"
    / "mini_dev"
    / "minidev"
    / "MINIDEV"
)
DEFAULT_RUN_DIR = STANDARD_DIR / "eval_runs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="使用 BIRD 官方实现评测 Mini-Dev R-VES。"
    )
    parser.add_argument(
        "--predictions",
        type=Path,
        default=DEFAULT_RUN_DIR / "bird_mini_dev_gold_as_prediction.json",
        help="BIRD 预测 SQL JSON 文件。",
    )
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=DEFAULT_RUN_DIR / "bird_mini_dev_sqlite_gold_normalized.sql",
        help="规范化后的 BIRD gold SQL 文件。",
    )
    parser.add_argument(
        "--db-root",
        type=Path,
        default=DEFAULT_DATASET_DIR / "dev_databases",
        help="Mini-Dev 数据库目录。",
    )
    parser.add_argument(
        "--difficulty",
        type=Path,
        default=DEFAULT_RUN_DIR / "bird_mini_dev_sqlite.jsonl",
        help="含 difficulty 字段的 Mini-Dev JSONL 文件。",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=DEFAULT_RUN_DIR / "bird_mini_dev_rves_gold_selftest.json",
        help="详细 JSON 结果路径。",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=DEFAULT_RUN_DIR / "bird_mini_dev_rves_gold_selftest.txt",
        help="文本报告路径。",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="每题重复计时次数，BIRD Mini-Dev README 建议 5。",
    )
    parser.add_argument(
        "--meta-time-out",
        type=float,
        default=3.0,
        help="官方超时系数；每题总超时为该值乘 iterations。",
    )
    parser.add_argument(
        "--num-cpus",
        type=int,
        default=min(4, os.cpu_count() or 1),
        help="并行进程数。",
    )
    parser.add_argument(
        "--clock",
        choices=("auto", "official-time", "perf-counter"),
        default="auto",
        help=(
            "计时源。auto 在 Windows 使用高分辨率 perf_counter，"
            "其他系统沿用官方 time.time。"
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="只评测前 N 题，用于冒烟测试；默认评测全部。",
    )
    return parser.parse_args()


def _resolve_clock(requested: str) -> str:
    if requested == "auto":
        return "perf-counter" if os.name == "nt" else "official-time"
    return requested


def _init_worker(clock: str) -> None:
    if clock == "perf-counter":
        # BIRD uses time.time().  On Windows that clock has a 15.625 ms
        # resolution and returns 0 seconds for many valid SQLite queries,
        # which then causes a division-by-zero error in the official ratio
        # calculation. QueryPerformanceCounter is the equivalent elapsed-
        # time clock with enough resolution for these queries.
        official_ves.time.time = time.perf_counter


def _worker(payload: tuple[str, str, str, int, int, float, str]) -> dict:
    return official_ves.execute_model(*payload)


def _validate_args(args: argparse.Namespace) -> None:
    for label, path in (
        ("预测 SQL", args.predictions),
        ("gold SQL", args.ground_truth),
        ("数据库目录", args.db_root),
        ("难度文件", args.difficulty),
    ):
        if not path.exists():
            raise FileNotFoundError(f"{label}不存在：{path}")
    if args.iterations <= 0:
        raise ValueError("--iterations 必须大于 0")
    if args.meta_time_out <= 0:
        raise ValueError("--meta-time-out 必须大于 0")
    if args.num_cpus <= 0:
        raise ValueError("--num-cpus 必须大于 0")
    if args.limit is not None and args.limit <= 0:
        raise ValueError("--limit 必须大于 0")


def _load_inputs(args: argparse.Namespace) -> tuple[list, list, list]:
    db_root = args.db_root.resolve().as_posix().rstrip("/") + "/"
    predictions, _ = official_ves.package_sqls(
        str(args.predictions.resolve()), db_root, mode="pred"
    )
    gold, db_paths = official_ves.package_sqls(
        str(args.ground_truth.resolve()), db_root, mode="gt"
    )
    with args.difficulty.open("r", encoding="utf-8") as handle:
        metadata = [json.loads(line) for line in handle if line.strip()]

    lengths = {
        "predictions": len(predictions),
        "ground_truth": len(gold),
        "db_paths": len(db_paths),
        "difficulty": len(metadata),
    }
    if len(set(lengths.values())) != 1:
        raise ValueError(f"输入条数不一致：{lengths}")

    missing_databases = [path for path in db_paths if not Path(path).is_file()]
    if missing_databases:
        preview = "\n".join(missing_databases[:5])
        raise FileNotFoundError(f"数据库文件缺失（最多显示 5 条）：\n{preview}")

    limit = args.limit or len(predictions)
    limit = min(limit, len(predictions))
    return predictions[:limit], gold[:limit], list(zip(db_paths, metadata))[:limit]


def _score(reward: float) -> float:
    return math.sqrt(reward) * 100


def _summarize(results: list[dict], metadata: list[dict]) -> dict:
    by_difficulty: dict[str, list[dict]] = defaultdict(list)
    for result, item in zip(results, metadata):
        by_difficulty[item["difficulty"]].append(result)

    ordered_levels = ("simple", "moderate", "challenging")
    difficulty_scores = {}
    for level in ordered_levels:
        subset = by_difficulty[level]
        difficulty_scores[level] = {
            "count": len(subset),
            "r_ves": official_ves.compute_ves(subset) if subset else None,
        }

    return {
        "count": len(results),
        "r_ves": official_ves.compute_ves(results),
        "nonzero_rewards": sum(item["reward"] != 0 for item in results),
        "zero_reward_indices": [
            item["sql_idx"] for item in results if item["reward"] == 0
        ],
        "reward_distribution": dict(
            sorted(Counter(str(item["reward"]) for item in results).items())
        ),
        "by_difficulty": difficulty_scores,
    }


def _write_outputs(
    args: argparse.Namespace,
    resolved_clock: str,
    results: list[dict],
    metadata: list[dict],
    elapsed_seconds: float,
) -> dict:
    summary = _summarize(results, metadata)
    details = []
    for result, item in zip(results, metadata):
        details.append(
            {
                "sql_idx": result["sql_idx"],
                "db_id": item.get("db_id"),
                "difficulty": item["difficulty"],
                "reward": result["reward"],
                "r_ves_score": _score(result["reward"]),
            }
        )

    payload = {
        "metric": "BIRD R-VES",
        "dataset": "BIRD Mini-Dev SQLite",
        "mode": "gold-to-gold self-test",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "official_implementation": str(
            (EVALUATION_DIR / "evaluation_ves.py").resolve()
        ),
        "config": {
            "iterations": args.iterations,
            "meta_time_out": args.meta_time_out,
            "task_timeout_seconds": args.iterations * args.meta_time_out,
            "num_cpus": args.num_cpus,
            "clock_requested": args.clock,
            "clock_resolved": resolved_clock,
            "clock_resolution_seconds": (
                time.get_clock_info("perf_counter").resolution
                if resolved_clock == "perf-counter"
                else time.get_clock_info("time").resolution
            ),
            "limit": args.limit,
            "predictions": str(args.predictions.resolve()),
            "ground_truth": str(args.ground_truth.resolve()),
            "db_root": str(args.db_root.resolve()),
            "difficulty": str(args.difficulty.resolve()),
        },
        "elapsed_seconds": elapsed_seconds,
        "summary": summary,
        "results": details,
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    rows = []
    for level in ("simple", "moderate", "challenging"):
        row = summary["by_difficulty"][level]
        score_text = "N/A" if row["r_ves"] is None else f'{row["r_ves"]:.2f}'
        rows.append(f"{level}: {score_text}（{row['count']} 条）")
    rows.append(f"总 R-VES: {summary['r_ves']:.2f}（{summary['count']} 条）")

    report = "\n".join(
        [
            "BIRD Mini-Dev R-VES Gold-to-Gold 自检",
            "=" * 48,
            f"重复计时次数: {args.iterations}",
            f"每题总超时: {args.iterations * args.meta_time_out:.1f} 秒",
            f"并行进程数: {args.num_cpus}",
            f"计时源: {resolved_clock}",
            f"运行耗时: {elapsed_seconds:.2f} 秒",
            "",
            *rows,
            f"非零奖励: {summary['nonzero_rewards']}/{summary['count']}",
            f"零奖励索引: {summary['zero_reward_indices']}",
            f"奖励分布: {summary['reward_distribution']}",
            "",
            "说明：每题得分为 sqrt(reward) × 100，总分为全部题目的平均值。",
        ]
    )
    args.output_report.write_text(report + "\n", encoding="utf-8")
    return summary


def main() -> int:
    args = parse_args()
    _validate_args(args)
    predictions, gold, db_and_metadata = _load_inputs(args)
    db_paths = [item[0] for item in db_and_metadata]
    metadata = [item[1] for item in db_and_metadata]
    resolved_clock = _resolve_clock(args.clock)
    payloads = [
        (
            predicted_sql,
            gold_sql,
            db_paths[index],
            index,
            args.iterations,
            args.meta_time_out,
            "SQLite",
        )
        for index, (predicted_sql, gold_sql) in enumerate(zip(predictions, gold))
    ]

    print(
        f"开始评测 {len(payloads)} 题：iterations={args.iterations}, "
        f"task_timeout={args.iterations * args.meta_time_out:.1f}s, "
        f"cpus={args.num_cpus}, clock={resolved_clock}",
        flush=True,
    )
    started = time.perf_counter()
    unordered_results = []
    with mp.Pool(
        processes=args.num_cpus,
        initializer=_init_worker,
        initargs=(resolved_clock,),
    ) as pool:
        for done, result in enumerate(
            pool.imap_unordered(_worker, payloads, chunksize=1), start=1
        ):
            unordered_results.append(result)
            if done == len(payloads) or done % 25 == 0:
                print(f"进度：{done}/{len(payloads)}", flush=True)

    elapsed_seconds = time.perf_counter() - started
    results = official_ves.sort_results(unordered_results)
    summary = _write_outputs(
        args, resolved_clock, results, metadata, elapsed_seconds
    )
    print(
        f"完成：R-VES={summary['r_ves']:.2f}，"
        f"非零奖励={summary['nonzero_rewards']}/{summary['count']}，"
        f"耗时={elapsed_seconds:.2f}s",
        flush=True,
    )
    print(f"JSON：{args.output_json.resolve()}")
    print(f"报告：{args.output_report.resolve()}")
    return 0


if __name__ == "__main__":
    mp.freeze_support()
    raise SystemExit(main())
