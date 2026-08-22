# db-access — 查表方式登记

每条为一个可读命名的条目，标明尝试优先级。凭据一律不落盘，只引用环境变量名。

## 条目列表

### 条目：`pg-local`（优先级 1）

- **数据源形态**：真实数据库
- **数据库**：PostgreSQL 18
- **库 / schema**：PGDATABASE（.env） / public
- **交互通道**：psql 命令行客户端
  - 路径：`C:\Program Files\PostgreSQL\18\bin\psql.exe`
- **凭据获取**：仓库根目录 `.env` 中的环境变量
  - 连接：`PGHOST`、`PGPORT`、`PGDATABASE`、`PGUSER`、`PGPASSWORD`
  - 其它：`PGSSLMODE`、`PGCLIENTENCODING`、`PGRESULT_ENCODING`、`PGCONNECT_TIMEOUT`、`PGSTATEMENT_TIMEOUT_MS`
- **只读边界**：
  - 账号为只读账号
  - 只允许 `SELECT` 与只读 `EXPLAIN`
  - 禁止 `INSERT`、`UPDATE`、`DELETE`、`DDL`、`COPY` 及一切写操作
  - 单次抽样最多 100 行
  - 查询必须设置超时（建议使用 .env 的 `PGSTATEMENT_TIMEOUT_MS` 或 psql 的 `-c "SET statement_timeout = ..."`）
- **封装脚本**：`scripts/` 下提供只读封装（见 scripts 说明）
- **尝试优先级**：1（当前唯一）
