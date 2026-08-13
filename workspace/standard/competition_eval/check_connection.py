from __future__ import annotations

from db_config import DatabaseConfig
from psql_runner import PsqlRunner


EXPECTED_TABLES = (
    "ads_cust_info_d",
    "dim_branch",
    "dim_product",
    "dim_public",
    "dwd_cust_hold_d",
    "dwd_cust_tran_d",
    "dws_cust_aset_d",
    "dws_cust_fin_d",
)


def main() -> int:
    config = DatabaseConfig.from_env()
    runner = PsqlRunner(config)
    identity = runner.check_identity()
    print(
        f"连接成功: user={identity['user']}, database={identity['database']}, "
        f"read_only={identity['read_only']}, timeout={identity['statement_timeout']}"
    )
    privileges = runner.check_table_permissions(EXPECTED_TABLES)
    found = {row["table_name"] for row in privileges}
    missing = sorted(set(EXPECTED_TABLES) - found)
    unsafe = [
        row["table_name"]
        for row in privileges
        if not row["can_select"] or row["can_write"]
    ]

    for row in privileges:
        print(
            f"  {row['table_name']}: SELECT={row['can_select']}, "
            f"WRITE={row['can_write']}"
        )

    if identity["read_only"] != "on" or missing or unsafe:
        missing = sorted(set(EXPECTED_TABLES) - found)
        if missing:
            print(f"缺少表: {', '.join(missing)}")
        if unsafe:
            print(f"权限不符合只读要求: {', '.join(unsafe)}")
        return 1

    print("远程 PostgreSQL 连接和只读权限检查通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
