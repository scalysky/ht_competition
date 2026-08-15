from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable

from workspace.standard.text2sql_runner.competition_data import CompetitionQuestion


SEPARATOR = "-" * 40


@dataclass(frozen=True)
class PredictionRecord:
    id: int
    sql: str | None
    fingerprint: str
    status: str
    error: str | None


@dataclass(frozen=True)
class OutputPaths:
    predictions: Path
    text: Path
    gold: Path
    errors: Path


def input_fingerprint(
    question: CompetitionQuestion,
    schema: str,
    model: str,
    messages: list[dict[str, str]],
) -> str:
    payload = {
        "question": asdict(question),
        "schema": schema,
        "model": model,
        "messages": messages,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def append_checkpoint(path: Path, record: PredictionRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(asdict(record), ensure_ascii=False, sort_keys=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _record_from_json(value: Any, path: Path, line_number: int) -> PredictionRecord:
    if not isinstance(value, dict):
        raise ValueError(f"检查点 {path} 第 {line_number} 行不是 JSON 对象")
    try:
        record = PredictionRecord(
            id=value["id"],
            sql=value["sql"],
            fingerprint=value["fingerprint"],
            status=value["status"],
            error=value["error"],
        )
    except KeyError as exc:
        raise ValueError(
            f"检查点 {path} 第 {line_number} 行缺少字段: {exc.args[0]}"
        ) from exc
    if not isinstance(record.id, int) or isinstance(record.id, bool):
        raise ValueError(f"检查点 {path} 第 {line_number} 行题号无效")
    if not isinstance(record.fingerprint, str) or not record.fingerprint:
        raise ValueError(f"检查点 {path} 第 {line_number} 行指纹无效")
    if record.status not in {"success", "error"}:
        raise ValueError(f"检查点 {path} 第 {line_number} 行状态无效")
    if record.status == "success" and not isinstance(record.sql, str):
        raise ValueError(f"检查点 {path} 第 {line_number} 行成功记录缺少 SQL")
    return record


def load_successful_checkpoints(
    path: Path,
) -> dict[tuple[int, str], PredictionRecord]:
    if not path.exists():
        return {}
    successful: dict[tuple[int, str], PredictionRecord] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                continue
            try:
                value = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"检查点 {path} 第 {line_number} 行不是有效 JSON"
                ) from exc
            record = _record_from_json(value, path, line_number)
            if record.status == "success":
                successful[(record.id, record.fingerprint)] = record
    return successful


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.replace(path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def write_run_metadata(
    output_dir: Path,
    *,
    knowledge_mode: str,
    knowledge_files: tuple[str, ...],
    model: str,
) -> Path:
    path = output_dir / "run_metadata.json"
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "knowledge_mode": knowledge_mode,
        "knowledge_files": list(knowledge_files),
        "model": model,
    }
    _atomic_write_text(path, _json_text(metadata))
    return path


def write_prediction_files(
    output_dir: Path,
    records: Iterable[PredictionRecord],
    source_gold_path: Path,
    selected_ids: list[int],
) -> OutputPaths:
    output_dir.mkdir(parents=True, exist_ok=True)
    record_list = sorted(records, key=lambda item: item.id)
    successful = [item for item in record_list if item.status == "success"]

    raw_gold = json.loads(source_gold_path.read_text(encoding="utf-8"))
    if not isinstance(raw_gold, list):
        raise ValueError("标准题目文件必须是 JSON 数组")
    gold_by_id = {
        item.get("id"): item
        for item in raw_gold
        if isinstance(item, dict) and isinstance(item.get("id"), int)
    }
    missing_gold = [case_id for case_id in selected_ids if case_id not in gold_by_id]
    if missing_gold:
        raise ValueError(f"标准题目缺少题号: {missing_gold}")

    paths = OutputPaths(
        predictions=output_dir / "predictions.json",
        text=output_dir / "predictions.txt",
        gold=output_dir / "gold_subset.json",
        errors=output_dir / "errors.json",
    )
    prediction_json = [{"id": item.id, "sql": item.sql} for item in successful]
    text_content = f"\n{SEPARATOR}\n".join(
        item.sql or "" for item in successful
    )
    if text_content:
        text_content += "\n"
    gold_subset = [gold_by_id[case_id] for case_id in selected_ids]
    error_json = [
        {"id": item.id, "error": item.error}
        for item in record_list
        if item.status == "error"
    ]

    _atomic_write_text(paths.predictions, _json_text(prediction_json))
    _atomic_write_text(paths.text, text_content)
    _atomic_write_text(paths.gold, _json_text(gold_subset))
    _atomic_write_text(paths.errors, _json_text(error_json))
    return paths
