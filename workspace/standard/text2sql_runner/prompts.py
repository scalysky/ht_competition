from __future__ import annotations

import re

from workspace.standard.competition_eval.sql_tools import (
    SqlSafetyError,
    validate_read_only_sql,
)
from workspace.standard.text2sql_runner.competition_data import CompetitionQuestion


SYSTEM_PROMPT = """你是金融客户营销场景的 PostgreSQL Text-to-SQL 助手。
请严格遵守以下规则：
1. 只返回一条可执行 SQL，不要解释，不要添加 Markdown 代码块。
2. SQL 必须是只读 SELECT，或最终返回 SELECT 结果的 WITH 查询。
3. 只能使用用户提供的表和字段，不得虚构表、字段或关联键。
4. 根据给出的主键和外键关系编写 JOIN，并忠实处理筛选、聚合、排序、去重、日期和 NULL 语义。
5. 使用 PostgreSQL 方言。"""


_FENCE_RE = re.compile(
    r"\A```(?:sql|postgresql)?[ \t]*\r?\n(?P<sql>.*?)\r?\n```\Z",
    re.IGNORECASE | re.DOTALL,
)
_READ_ONLY_START_RE = re.compile(r"\A(?:select|with)\b", re.IGNORECASE)


def build_messages(
    question: CompetitionQuestion,
    schema: str,
) -> list[dict[str, str]]:
    if not schema.strip():
        raise ValueError("数据库结构为空")
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"问题编号：{question.id}\n"
                f"问题：{question.question}\n\n"
                f"{schema}\n\n"
                "请生成 PostgreSQL 查询。"
            ),
        },
    ]


def clean_model_sql(content: str) -> str:
    if not isinstance(content, str) or not content.strip():
        raise SqlSafetyError("SQL 为空")

    cleaned = content.strip()
    fenced = _FENCE_RE.fullmatch(cleaned)
    if fenced:
        cleaned = fenced.group("sql").strip()
    elif "```" in cleaned:
        raise SqlSafetyError("只允许返回 SQL，不允许附带解释或不完整代码块")

    if not cleaned or not _READ_ONLY_START_RE.match(cleaned):
        raise SqlSafetyError("只允许返回 SQL，不允许附带解释")
    validate_read_only_sql(cleaned)
    return cleaned
