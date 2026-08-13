from __future__ import annotations

from pathlib import Path

from evaluate import main as evaluate_main


QUERY_FILE = Path(__file__).with_name("gold_queries.json")
REPORT_FILE = Path(__file__).parents[1] / "eval_runs" / "competition_gold_validation.json"


if __name__ == "__main__":
    raise SystemExit(
        evaluate_main(
            [
                "--gold",
                str(QUERY_FILE),
                "--predictions",
                str(QUERY_FILE),
                "--metrics",
                "em,ex",
                "--output",
                str(REPORT_FILE),
            ]
        )
    )
