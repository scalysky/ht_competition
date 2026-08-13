from __future__ import annotations

from dataclasses import dataclass
import re


class SqlSafetyError(ValueError):
    """Raised when an input is not a single read-only SELECT statement."""


@dataclass(frozen=True)
class SqlToken:
    kind: str
    text: str


_WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_$]*")
_NUMBER_RE = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
_DOLLAR_TAG_RE = re.compile(r"\$(?:[A-Za-z_][A-Za-z0-9_]*)?\$")
_MULTI_CHAR_OPERATORS = (
    "#>>",
    "->>",
    "::",
    ">=",
    "<=",
    "<>",
    "!=",
    "||",
    "->",
    "#>",
    ":=",
    "=>",
)

_FORBIDDEN_WORDS = {
    "alter",
    "analyze",
    "call",
    "cluster",
    "comment",
    "copy",
    "create",
    "deallocate",
    "delete",
    "discard",
    "do",
    "drop",
    "execute",
    "grant",
    "insert",
    "into",
    "listen",
    "lock",
    "merge",
    "notify",
    "prepare",
    "refresh",
    "reindex",
    "reset",
    "revoke",
    "set",
    "truncate",
    "unlisten",
    "update",
    "vacuum",
}


def _consume_quoted(sql: str, start: int, quote: str) -> int:
    index = start + 1
    while index < len(sql):
        if sql[index] == quote:
            if index + 1 < len(sql) and sql[index + 1] == quote:
                index += 2
                continue
            return index + 1
        index += 1
    raise SqlSafetyError("SQL 字符串或引用标识符未闭合")


def _consume_block_comment(sql: str, start: int) -> int:
    depth = 1
    index = start + 2
    while index < len(sql) and depth:
        if sql.startswith("/*", index):
            depth += 1
            index += 2
        elif sql.startswith("*/", index):
            depth -= 1
            index += 2
        else:
            index += 1
    if depth:
        raise SqlSafetyError("SQL 块注释未闭合")
    return index


def tokenize_sql(sql: str) -> list[SqlToken]:
    if not isinstance(sql, str):
        raise SqlSafetyError("SQL 必须是字符串")

    tokens: list[SqlToken] = []
    index = 0
    while index < len(sql):
        char = sql[index]
        if char.isspace():
            index += 1
            continue
        if sql.startswith("--", index):
            newline = sql.find("\n", index + 2)
            index = len(sql) if newline == -1 else newline + 1
            continue
        if sql.startswith("/*", index):
            index = _consume_block_comment(sql, index)
            continue
        if char == "'":
            end = _consume_quoted(sql, index, "'")
            tokens.append(SqlToken("string", sql[index:end]))
            index = end
            continue
        if char == '"':
            end = _consume_quoted(sql, index, '"')
            tokens.append(SqlToken("quoted_identifier", sql[index:end]))
            index = end
            continue
        if char == "$":
            match = _DOLLAR_TAG_RE.match(sql, index)
            if match:
                tag = match.group(0)
                end = sql.find(tag, match.end())
                if end == -1:
                    raise SqlSafetyError("SQL dollar-quoted 字符串未闭合")
                end += len(tag)
                tokens.append(SqlToken("string", sql[index:end]))
                index = end
                continue
        word = _WORD_RE.match(sql, index)
        if word:
            tokens.append(SqlToken("word", word.group(0)))
            index = word.end()
            continue
        number = _NUMBER_RE.match(sql, index)
        if number:
            tokens.append(SqlToken("number", number.group(0)))
            index = number.end()
            continue
        operator = next(
            (value for value in _MULTI_CHAR_OPERATORS if sql.startswith(value, index)),
            None,
        )
        if operator:
            tokens.append(SqlToken("operator", operator))
            index += len(operator)
            continue
        tokens.append(SqlToken("symbol", char))
        index += 1
    return tokens


def validate_read_only_sql(sql: str) -> None:
    tokens = tokenize_sql(sql)
    if not tokens:
        raise SqlSafetyError("SQL 为空")

    semicolon_positions = [i for i, token in enumerate(tokens) if token.text == ";"]
    if semicolon_positions:
        if len(semicolon_positions) != 1 or semicolon_positions[0] != len(tokens) - 1:
            raise SqlSafetyError("只允许单条 SQL，不允许多语句执行")
        tokens = tokens[:-1]
    if not tokens:
        raise SqlSafetyError("SQL 为空")

    words = [token.text.lower() for token in tokens if token.kind == "word"]
    if not words or words[0] not in {"select", "with"}:
        raise SqlSafetyError("SQL 必须以 SELECT 或 WITH 开头")

    forbidden = sorted(set(words) & _FORBIDDEN_WORDS)
    if forbidden:
        raise SqlSafetyError(f"SQL 包含禁止关键字: {', '.join(forbidden)}")


def strip_terminal_semicolon(sql: str) -> str:
    tokens = tokenize_sql(sql)
    if tokens and tokens[-1].text == ";":
        return sql[: sql.rfind(";")].rstrip()
    return sql.strip()


def normalize_sql(sql: str) -> str:
    """Canonical lexical form for PostgreSQL normalized exact match."""
    tokens = tokenize_sql(sql)
    if tokens and tokens[-1].text == ";":
        tokens = tokens[:-1]
    normalized = [
        token.text.lower() if token.kind == "word" else token.text
        for token in tokens
    ]
    return " ".join(normalized)

