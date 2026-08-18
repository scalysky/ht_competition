#!/usr/bin/env python3
"""Read-only PostgreSQL query runner for at2s db-access.

Loads connection params (PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD) from the
.env file in the db-access directory (parent of this script's folder), then
runs a single read-only SQL statement and writes the result tab-separated
(header row included) to stdout as UTF-8 bytes.

Usage:
    pg_query.py "<SQL>" [row_limit, default 100]

Only SELECT / WITH / EXPLAIN / SHOW statements are permitted. Anything else is
rejected before touching the database. The connection is opened read-only and
sslmode defaults to "disable" (the server does not negotiate TLS).

Output is written as raw UTF-8 bytes to sys.stdout.buffer so that Chinese text
is preserved regardless of the caller's console code page.
"""
import os
import re
import sys

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

ALLOWED = re.compile(r"^\s*(SELECT|WITH|EXPLAIN|SHOW)\b", re.IGNORECASE)


def _out(line):
    sys.stdout.buffer.write((line + "\n").encode("utf-8"))


def _err(line):
    try:
        sys.stderr.buffer.write((line + "\n").encode("utf-8"))
    except Exception:  # noqa: BLE001
        pass


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bytes):
        try:
            return v.decode("utf-8")
        except UnicodeDecodeError:
            return v.decode("latin-1")
    return str(v)


def load_env(path):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


def main():
    if len(sys.argv) < 2:
        _err('usage: pg_query.py "<SQL>" [row_limit]')
        sys.exit(2)
    sql = sys.argv[1]
    try:
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    except ValueError:
        _err("ERROR: row_limit must be an integer")
        sys.exit(2)

    if not ALLOWED.match(sql):
        _err("ERROR: only SELECT / WITH / EXPLAIN / SHOW are allowed (read-only)")
        sys.exit(2)

    try:
        import psycopg
    except ImportError:
        _err("ERROR: psycopg is not installed in this interpreter")
        sys.exit(3)

    load_env(ENV_PATH)

    try:
        conn = psycopg.connect(
            host=os.environ.get("PGHOST"),
            port=os.environ.get("PGPORT"),
            dbname=os.environ.get("PGDATABASE"),
            user=os.environ.get("PGUSER"),
            password=os.environ.get("PGPASSWORD"),
            connect_timeout=15,
            sslmode=os.environ.get("PGSSLMODE", "disable"),
        )
    except Exception as exc:  # noqa: BLE001
        _err(f"ERROR: connection failed: {exc}")
        sys.exit(4)

    conn.read_only = True
    cur = conn.cursor()
    try:
        cur.execute(sql)
    except Exception as exc:  # noqa: BLE001
        conn.close()
        _err(f"ERROR: query failed: {exc}")
        sys.exit(5)

    if cur.description is None:
        _out("(no rows returned)")
        conn.close()
        sys.exit(0)

    headers = [d.name for d in cur.description]
    _out("\t".join(headers))
    for row in cur.fetchmany(limit):
        _out("\t".join(_cell(v) for v in row))
    conn.close()
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
