# access.md — 查表方式

本文件记录本环境下可用的查表方式。**只记交互方式，不记凭据。** 凭据存于同目录 `.env`（已 gitignore），由 `scripts/pg_query.py` 自动加载。

## 条目 1：remote-postgresql（优先级 1）

- **数据源**：远程 PostgreSQL 15.18（Anolis OS），地址 `47.94.129.195:5432`，初始库 `root`，schema `public`
- **表清单**：8 张业务表 —— `ads_cust_info_d`、`dim_branch`、`dim_product`、`dim_public`、`dwd_cust_hold_d`、`dwd_cust_tran_d`、`dws_cust_aset_d`、`dws_cust_fin_d`
- **账号**：只读用户 `read`
- **凭据**：不落盘到本文件。连接参数（PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD）存于同目录 `.env`（已 gitignore），由脚本自动加载；若环境变量已存在同名值则优先使用环境变量
- **从零复现连接**：仓库提供同目录 `.env.example`（含 host/port/db/user 等连接配置，**不含密码**）。新克隆时复制为 `.env` 并填入只读账户密码即可；也可直接以同名环境变量提供。连接配置：`47.94.129.195:5432` / 库 `root` / schema `public` / 用户 `read` / `sslmode=disable`
- **解释器**：`skills/db-access/.venv-win/`（Windows venv，Python 3.12 + psycopg 3.3）
- **执行脚本**：`skills/db-access/scripts/pg_query.py`，用法：`pg_query.py "<SQL>" [行数上限，默认 100]`

### 执行流程

1. 用 `.venv-win\Scripts\python.exe` 运行 `scripts/pg_query.py "<SQL>"`
2. 脚本自动从同目录 `.env` 读取 `PGHOST` / `PGPORT` / `PGDATABASE` / `PGUSER` / `PGPASSWORD` 补全连接参数（已存在的环境变量优先）
3. 以只读会话连接（`conn.read_only = True`，且 `sslmode` 默认 `disable`，因服务端不做 TLS 协商；可用环境变量 `PGSSLMODE` 覆盖）
4. 输出制表符分隔结果（含表头），默认上限 100 行；结果以 UTF-8 字节写入 stdout（中文安全）
5. 仅允许 `SELECT` / `WITH` / `EXPLAIN` / `SHOW`，其它语句在连库前即被拒绝

### 约束

- 只读；每查询带行数上限；码值字段看去重取值时可显式调大第二参数
- 凭据不写入本文件、不回显；`.env` 已 gitignore
- `scripts/pg_query.py` 通过 `sys.stdout.buffer` 直接写 UTF-8，规避 Windows 控制台代码页，确保中文抽样结果在任意调用方都不乱码

### 验证记录

- `SELECT version()` 返回 `PostgreSQL 15.18 ... (Anolis OS ...)`；`pg_tables` 列出上述 8 张表，连接与读取均正常
- 中文抽样验证：`dim_public.describe`、`dim_branch.org_name` 等含中文字段经脚本输出后中文完整无乱码
