from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENV_FILE = REPO_ROOT / ".env"


def load_env_file(path: Path = DEFAULT_ENV_FILE) -> None:
    """Load a small .env file without overriding existing process variables."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
    sslmode: str
    client_encoding: str
    result_encoding: str
    connect_timeout: int
    statement_timeout_ms: int

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        load_env_file()
        required = ("PGHOST", "PGDATABASE", "PGUSER", "PGPASSWORD")
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            names = ", ".join(missing)
            raise RuntimeError(f".env 缺少必填项: {names}")

        return cls(
            host=os.environ["PGHOST"],
            port=int(os.getenv("PGPORT", "5432")),
            database=os.environ["PGDATABASE"],
            user=os.environ["PGUSER"],
            password=os.environ["PGPASSWORD"],
            sslmode=os.getenv("PGSSLMODE", "prefer"),
            client_encoding=os.getenv("PGCLIENTENCODING", "UTF8"),
            result_encoding=os.getenv("PGRESULT_ENCODING", "utf-8"),
            connect_timeout=int(os.getenv("PGCONNECT_TIMEOUT", "10")),
            statement_timeout_ms=int(os.getenv("PGSTATEMENT_TIMEOUT_MS", "30000")),
        )


