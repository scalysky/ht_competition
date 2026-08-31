# access — 查表方式

## 1. pg_query（优先级 1，已验证可用）

- 通道：Python 脚本 `scripts/pg_query.py`（psycopg 直连，只读白名单：SELECT / WITH / TABLE / EXPLAIN / SHOW）
- 解释器：本目录 `.venv-win\Scripts\python.exe`（psycopg 已装在该 venv；系统 Python 无 psycopg）
- 凭据：本目录 `.env`（PGHOST / PGPORT / PGDATABASE / PGUSER / PGPASSWORD），脚本自动加载，不在本文件记录
- 用法：`<venv-win 解释器> scripts\pg_query.py "<SQL>" [行数上限]`，行数上限默认 100
- 服务器特性：PostgreSQL 15.18，库编码 **SQL_ASCII**，数据为 UTF-8 字节。脚本已内置 `client_encoding=utf8` 与 stdout UTF-8 重配置；缺少时中文查询条件会报 UnicodeEncodeError、中文结果显示乱码
- 验证记录：2026-08-19 连通性、中文取值（dim_public/dim_product/ads_cust_info_d）均实测通过
