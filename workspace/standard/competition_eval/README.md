# 比赛 PostgreSQL Text-to-SQL 统一评分器

本目录提供比赛数据的 EM、EX 和 R-VES 统一评分。评分器使用 PostgreSQL
自带的 `psql`，Python 代码只依赖标准库，不需要安装额外的数据库驱动。

## 目录内容

- `gold_queries.json`：Q&A.xlsx 中的 7 条问题和标准 SQL。
- `evaluate.py`：EM、EX、R-VES 统一评分入口。
- `check_connection.py`：连接与 8 张表的只读权限检查。
- `validate_gold_queries.py`：使用标准 SQL 同时作为预测 SQL 的 EM/EX 冒烟测试。
- `tests/`：SQL 安全、EM 规范化、EX 结果比较和 R-VES 奖励分段测试。

## 数据库配置

复制仓库根目录的 `.env.example` 为 `.env`，填写只读账号。真实 `.env`
已被 Git 忽略，不得提交密码。

```dotenv
PGHOST=your-postgresql-host
PGPORT=5432
PGDATABASE=your-database
PGUSER=your-readonly-user
PGPASSWORD=your-local-password
PGSSLMODE=prefer
PGCLIENTENCODING=UTF8
PGRESULT_ENCODING=utf-8
PGCONNECT_TIMEOUT=10
PGSTATEMENT_TIMEOUT_MS=30000
```

当前远程比赛库的服务器编码是 `SQL_ASCII`，实际中文结果为 UTF-8 字节，
因此本机 `.env` 使用：

```dotenv
PGCLIENTENCODING=SQL_ASCII
PGRESULT_ENCODING=utf-8
```

## 检查连接与只读权限

```powershell
python workspace/standard/competition_eval/check_connection.py
```

必须满足：

- `default_transaction_read_only=on`；
- 8 张业务表全部拥有 `SELECT` 权限；
- 8 张表均无 `INSERT/UPDATE/DELETE/TRUNCATE` 权限；
- 单条 SQL 默认 30 秒超时。

## 预测文件格式

推荐使用 JSON 数组：

```json
[
  {"id": 1, "sql": "SELECT ..."},
  {"id": 2, "sql": "WITH ... SELECT ..."}
]
```

也支持 ID 到 SQL 的 JSON 对象：

```json
{
  "1": "SELECT ...",
  "2": "WITH ... SELECT ..."
}
```

缺少预测、SQL 语法错误、超时或安全校验失败都会在该题记 0 分，不会中断
其他题目的评测。

## 运行统一评分

```powershell
python workspace/standard/competition_eval/evaluate.py `
  --predictions path/to/model_predictions.json `
  --metrics em,ex,rves `
  --ves-iterations 5 `
  --ves-warmups 1
```

默认标准文件为 `gold_queries.json`，默认报告为
`workspace/standard/eval_runs/competition_evaluation.json`。每次同时生成：

- JSON：完整配置、汇总指标、逐题 SQL、错误与时间比。
- CSV：便于用 Excel 汇总多模型结果。
- Markdown：便于直接放入实验报告。

只运行 EM/EX：

```powershell
python workspace/standard/competition_eval/evaluate.py `
  --predictions path/to/model_predictions.json `
  --metrics em,ex
```

## 指标口径

### EM

本比赛的 EM 是 PostgreSQL SQL 规范化精确匹配：

- 忽略注释、空白、未引用关键字/标识符大小写和末尾分号；
- 保留字符串字面量、运算符、表达式、列和子句顺序；
- 因此语义相同但写法不同的 SQL 可能 EM=0、EX=1。

Spider 官方 EM 依赖 Spider 专用 schema 和 SQLite 解析器，不能完整解析本比赛的
PostgreSQL CTE、`::` 类型转换和函数，因此比赛数据采用上述可重现口径。

### EX

默认对齐 BIRD 官方 `set(predicted_res) == set(gold_res)` 口径：

- 忽略行顺序；
- 忽略重复行次数；
- 保留列顺序和结果值类型。

某道题如果必须检查顺序或重复行，可在标准样本中增加：

```json
{"order_sensitive": true, "duplicate_sensitive": true}
```

### R-VES

只有 EX=1 才计算 R-VES，否则为 0。执行时间使用 PostgreSQL
`EXPLAIN (ANALYZE, TIMING FALSE, FORMAT JSON)` 返回的服务器端 `Execution Time`，
不把远程网络延迟算入 SQL 耗时。

时间比为 `gold_time / predicted_time`，奖励分段与 BIRD 官方一致：

| 时间比 | reward |
|---:|---:|
| `>= 2` | 1.25 |
| `[1, 2)` | 1.00 |
| `[0.5, 1)` | 0.75 |
| `[0.25, 0.5)` | 0.50 |
| `< 0.25` | 0.25 |

单题得分为 `sqrt(reward) * 100`，总 R-VES 是全部题目得分平均值。因为奖励分段
对 1.0 附近的耗时抖动敏感，即使预测 SQL 与标准 SQL 完全一致，单次 R-VES
也可能低于 100；正式对比必须使用相同的重复次数和数据库环境。

## 安全措施

- 只接受单条 `SELECT` 或只读 `WITH ... SELECT`。
- 执行前拒绝 DML、DDL、`COPY`、`CALL`、`DO`、`SELECT INTO` 和多语句。
- 每次连接强制只读事务、30 秒 SQL 超时、5 秒锁超时和 `public` 搜索路径。
- 数据库账号本身仅有 8 张表的 `SELECT` 权限。
- 密码只通过子进程环境变量传递，不写入命令行、评测报告或 Git。

## 自测

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest discover `
  -s workspace/standard/competition_eval/tests `
  -v
```

Gold-to-Gold EM/EX：

```powershell
python workspace/standard/competition_eval/validate_gold_queries.py
```

Gold-to-Gold 全指标：

```powershell
python workspace/standard/competition_eval/evaluate.py `
  --predictions workspace/standard/competition_eval/gold_queries.json `
  --metrics em,ex,rves `
  --output workspace/standard/eval_runs/competition_gold_full_self_test.json
```

## 已知数据问题

第 3、5、7 题的标准 SQL 在当前数据上返回空结果。评分器会用
`empty_result_match=true` 标记。空结果会降低 EX 的区分能力，正式数据集应尽量调整
题目或补充能命中的数据。

