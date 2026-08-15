from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CompetitionQuestion:
    id: int
    question: str


def load_questions(path: Path) -> list[CompetitionQuestion]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("题目文件必须是 JSON 数组")

    questions: list[CompetitionQuestion] = []
    seen_ids: set[int] = set()
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"第 {index} 条题目必须是 JSON 对象")
        case_id = item.get("id")
        question = item.get("question")
        if not isinstance(case_id, int) or isinstance(case_id, bool) or case_id <= 0:
            raise ValueError(f"第 {index} 条题号必须是正整数")
        if case_id in seen_ids:
            raise ValueError(f"题号重复: {case_id}")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"题目 #{case_id} 的问题为空")
        seen_ids.add(case_id)
        questions.append(CompetitionQuestion(id=case_id, question=question.strip()))
    return sorted(questions, key=lambda item: item.id)


def format_schema(metadata: dict[str, Any]) -> str:
    tables = metadata.get("tables")
    if not isinstance(tables, list) or not tables:
        raise RuntimeError("未读取到 public schema")

    lines = ["表结构："]
    for table in sorted(tables, key=lambda item: item["name"]):
        columns = sorted(
            table.get("columns", []),
            key=lambda item: item.get("ordinal_position", 0),
        )
        rendered_columns = []
        for column in columns:
            nullable = "" if column.get("nullable", True) else " NOT NULL"
            rendered_columns.append(
                f"{column['name']} {column['type']}{nullable}"
            )
        lines.append(f"- {table['name']}({', '.join(rendered_columns)})")

    primary_keys = []
    for table in sorted(tables, key=lambda item: item["name"]):
        columns = table.get("primary_key", [])
        if columns:
            primary_keys.append(f"{table['name']}.{', '.join(columns)}")
    if primary_keys:
        lines.append("主键：")
        lines.extend(f"- PRIMARY KEY: {value}" for value in primary_keys)

    foreign_keys = metadata.get("foreign_keys", [])
    if foreign_keys:
        lines.append("外键：")
        for foreign_key in sorted(
            foreign_keys,
            key=lambda item: (
                item["table"],
                item["column"],
                item["references_table"],
                item["references_column"],
            ),
        ):
            lines.append(
                "- FOREIGN KEY: "
                f"{foreign_key['table']}.{foreign_key['column']} -> "
                f"{foreign_key['references_table']}."
                f"{foreign_key['references_column']}"
            )
    return "\n".join(lines)
