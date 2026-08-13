from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Hashable

from db_config import DatabaseConfig
from sql_tools import strip_terminal_semicolon, validate_read_only_sql


class PsqlExecutionError(RuntimeError):
    def __init__(self, message: str, *, category: str = "execution_error") -> None:
        super().__init__(message)
        self.category = category


class JsonObject(list):
    """Ordered JSON object pairs, including duplicate keys."""


@dataclass(frozen=True)
class QueryRows:
    rows: list[Hashable]
    row_count: int


def _canonical_value(value: Any) -> Hashable:
    if isinstance(value, JsonObject):
        return ("object", tuple((key, _canonical_value(item)) for key, item in value))
    if isinstance(value, list):
        return ("array", tuple(_canonical_value(item) for item in value))
    if isinstance(value, Decimal):
        if value == 0:
            value = Decimal(0)
        return ("number", value.normalize())
    if value is None:
        return ("null",)
    if isinstance(value, bool):
        return ("boolean", value)
    if isinstance(value, str):
        return ("string", value)
    return (type(value).__name__, value)


def _json_object_pairs(pairs: list[tuple[str, Any]]) -> JsonObject:
    return JsonObject(pairs)


class PsqlRunner:
    def __init__(
        self,
        config: DatabaseConfig,
        *,
        psql_path: str | None = None,
    ) -> None:
        self.config = config
        self.psql_path = self._locate_psql(psql_path)

    @staticmethod
    def _locate_psql(explicit: str | None) -> str:
        candidates = [
            explicit,
            os.getenv("PSQL_PATH"),
            shutil.which("psql"),
            r"C:\Program Files\PostgreSQL\18\bin\psql.exe",
            r"C:\Program Files\PostgreSQL\17\bin\psql.exe",
            r"C:\Program Files\PostgreSQL\16\bin\psql.exe",
        ]
        for candidate in candidates:
            if candidate and Path(candidate).is_file():
                return str(candidate)
        raise RuntimeError("未找到 psql，请通过 --psql-path 指定可执行文件")

    def _environment(self) -> dict[str, str]:
        env = os.environ.copy()
        env.update(
            {
                "PGPASSWORD": self.config.password,
                "PGSSLMODE": self.config.sslmode,
                "PGCONNECT_TIMEOUT": str(self.config.connect_timeout),
                "PGCLIENTENCODING": self.config.client_encoding,
                "PGOPTIONS": (
                    "-c default_transaction_read_only=on "
                    f"-c statement_timeout={self.config.statement_timeout_ms} "
                    "-c lock_timeout=5000 -c search_path=public"
                ),
            }
        )
        return env

    def _run(self, sql: str) -> str:
        command = [
            self.psql_path,
            "-X",
            "-q",
            "-A",
            "-t",
            "-P",
            "pager=off",
            "-h",
            self.config.host,
            "-p",
            str(self.config.port),
            "-U",
            self.config.user,
            "-d",
            self.config.database,
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            sql,
        ]
        process_timeout = self.config.connect_timeout + self.config.statement_timeout_ms / 1000 + 10
        try:
            completed = subprocess.run(
                command,
                env=self._environment(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=process_timeout,
                check=False,
                creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
            )
        except subprocess.TimeoutExpired as exc:
            raise PsqlExecutionError("评测进程超时", category="process_timeout") from exc

        stdout = completed.stdout.decode(
            self.config.result_encoding,
            errors="surrogateescape",
        )
        stderr = completed.stderr.decode(
            self.config.result_encoding,
            errors="replace",
        ).strip()
        if completed.returncode != 0:
            lowered = stderr.lower()
            category = "statement_timeout" if "statement timeout" in lowered else "execution_error"
            raise PsqlExecutionError(stderr or "psql 执行失败", category=category)
        return stdout.strip()

    def check_identity(self) -> dict[str, str]:
        output = self._run(
            "SELECT current_user, current_database(), "
            "current_setting('default_transaction_read_only'), "
            "current_setting('statement_timeout')"
        )
        parts = output.split("|")
        if len(parts) != 4:
            raise PsqlExecutionError(f"无法解析连接信息: {output}")
        return dict(zip(("user", "database", "read_only", "statement_timeout"), parts))

    def check_table_permissions(self, table_names: tuple[str, ...]) -> list[dict[str, Any]]:
        if not table_names or any(not name.replace("_", "").isalnum() for name in table_names):
            raise ValueError("表名列表无效")
        quoted_names = ", ".join("'" + name.replace("'", "''") + "'" for name in table_names)
        output = self._run(
            "SELECT table_name, "
            "has_table_privilege(current_user, format('%I.%I', table_schema, table_name), 'SELECT'), "
            "has_table_privilege(current_user, format('%I.%I', table_schema, table_name), "
            "'INSERT,UPDATE,DELETE,TRUNCATE') "
            "FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name IN ("
            + quoted_names
            + ") ORDER BY table_name"
        )
        permissions: list[dict[str, Any]] = []
        for line in output.splitlines() if output else []:
            parts = line.split("|")
            if len(parts) != 3:
                raise PsqlExecutionError(f"无法解析表权限: {line}")
            permissions.append(
                {
                    "table_name": parts[0],
                    "can_select": parts[1] == "t",
                    "can_write": parts[2] == "t",
                }
            )
        return permissions

    def execute_rows(self, sql: str) -> QueryRows:
        validate_read_only_sql(sql)
        inner_sql = strip_terminal_semicolon(sql)
        output = self._run(
            "COPY (SELECT row_to_json(_eval_row) FROM ("
            + inner_sql
            + ") AS _eval_row) TO STDOUT"
        )
        if not output:
            return QueryRows(rows=[], row_count=0)

        rows: list[Hashable] = []
        for line in output.splitlines():
            parsed = json.loads(
                line,
                parse_float=Decimal,
                parse_int=Decimal,
                object_pairs_hook=_json_object_pairs,
            )
            if not isinstance(parsed, JsonObject):
                raise PsqlExecutionError("查询结果不是 JSON 对象")
            row = tuple(_canonical_value(value) for _, value in parsed)
            rows.append(row)
        return QueryRows(rows=rows, row_count=len(rows))

    def execution_time_ms(self, sql: str) -> float:
        validate_read_only_sql(sql)
        inner_sql = strip_terminal_semicolon(sql)
        output = self._run(
            "EXPLAIN (ANALYZE TRUE, TIMING FALSE, SUMMARY TRUE, FORMAT JSON) " + inner_sql
        )
        try:
            plan = json.loads(output, parse_float=Decimal, parse_int=Decimal)
            return float(plan[0]["Execution Time"])
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise PsqlExecutionError(f"无法解析 EXPLAIN 执行时间: {output[:500]}") from exc
