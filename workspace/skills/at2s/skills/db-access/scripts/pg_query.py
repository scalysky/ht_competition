import os
import sys

import psycopg

READ_ONLY_PREFIXES = ("select", "with", "table ", "explain", "show")


def load_env_file():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    try:
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())
    except FileNotFoundError:
        pass


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    load_env_file()
    sql = sys.argv[1] if len(sys.argv) > 1 else "SELECT version()"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    stripped = sql.lstrip("( \n\r\t").lower()
    if not stripped.startswith(READ_ONLY_PREFIXES):
        sys.exit("rejected: non-read-only statement")
    conn = psycopg.connect(
        host=os.environ["PGHOST"],
        port=os.environ.get("PGPORT", "5432"),
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        connect_timeout=10,
        client_encoding="utf8",
    )
    try:
        conn.read_only = True
        with conn.cursor() as cur:
            cur.execute(sql)
            cols = [d.name for d in cur.description] if cur.description else []
            rows = cur.fetchmany(limit)
        if cols:
            print("\t".join(cols))
        for row in rows:
            print("\t".join(
                "" if v is None else (v.decode("utf-8", "replace") if isinstance(v, (bytes, bytearray)) else str(v))
                for v in row
            ))
        print(f"-- {len(rows)} row(s)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
