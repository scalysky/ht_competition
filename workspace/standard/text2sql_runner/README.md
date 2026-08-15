# 比赛 Text-to-SQL 一键生成与评测

该工具只处理比赛 PostgreSQL 业务题，不调用模型运行 Spider 或 BIRD。它会把比赛题目、实时数据库表结构和经过验证的表关联知识发送给 OpenAI 兼容模型，逐题生成 SQL，然后调用现有评分器计算 EM、EX 和 R-VES。

模型不会收到 `gold_queries.json` 中的标准 SQL。正式生成期间，评分结果也不会反馈给模型。

## 1. 准备环境

需要：

- Python 3.11 或更高版本；
- PostgreSQL 的 `psql.exe`；
- 已验证的远程 PostgreSQL 只读账号；
- 一个支持 `/chat/completions` 的 OpenAI 兼容模型接口。

在仓库根目录复制配置模板：

```powershell
Copy-Item .env.example .env
```

编辑本地 `.env`。保留现有 PostgreSQL 配置，并填写：

```dotenv
LLM_BASE_URL=https://your-openai-compatible-host/v1
LLM_API_KEY=replace-with-local-api-key
LLM_MODEL=replace-with-model-name
LLM_TIMEOUT_SECONDS=120
```

`.env` 已被 Git 忽略，不要把真实 API Key 写入 `.env.example`、命令行或报告。

## 2. 查看帮助

```powershell
cd C:\Code\Fin_tech_match\ht_competition
.\run_text2sql.ps1 -Help
```

## 3. 先测试一道题

这一步会产生一次真实模型调用费用：

```powershell
.\run_text2sql.ps1 -Limit 1 -RunName smoke
```

脚本会自动：

1. 检查 PostgreSQL 连接是否为只读；
2. 读取 `public` schema；
3. 加载表关联和业务注意事项；
4. 调用模型生成第一题 SQL；
5. 保存预测和检查点；
6. 计算该题 EM、EX 和 R-VES；
7. 生成 JSON、CSV 和 Markdown 报告。

## 4. 运行全部比赛题

确认单题结果正常后运行当前全部7题：

```powershell
.\run_text2sql.ps1 -Full -RunName baseline
```

必须明确传入 `-Limit N` 或 `-Full`，防止误触发批量付费请求。

## 5. 断点续跑

同一个 `RunName` 默认自动读取 `checkpoint.jsonl`。只有题目、schema、提示词和模型都没有变化时，已成功题目才会跳过：

```powershell
.\run_text2sql.ps1 -Full -RunName baseline
```

失败题会重新调用，成功题不会重复计费。如果不想复用旧检查点：

```powershell
.\run_text2sql.ps1 -Full -NoResume
```

未指定 `RunName` 时，`-NoResume` 会创建时间戳目录。

## 6. 只生成或只评测

只调用模型生成 SQL：

```powershell
.\run_text2sql.ps1 -Full -RunName baseline -GenerateOnly
```

对已有预测重新评分，不调用模型：

```powershell
.\run_text2sql.ps1 -Full -RunName baseline -EvaluateOnly
```

## 7. 输出文件

默认目录：

```text
workspace/standard/eval_runs/competition/<RunName>/
├─ checkpoint.jsonl
├─ predictions.json
├─ predictions.txt
├─ gold_subset.json
├─ errors.json
├─ evaluation.json
├─ evaluation.csv
└─ evaluation.md
```

- `predictions.json`：评分器使用的题号与 SQL；
- `predictions.txt`：只包含 SQL，答案之间严格使用40个 `-`；
- `checkpoint.jsonl`：每完成一道题立即写入，用于断点续跑；
- `errors.json`：失败题及错误原因；
- `evaluation.*`：EM、EX、R-VES 汇总和逐题结果。

`predictions.txt` 示例：

```text
SELECT ...
----------------------------------------
SELECT ...
```

文件末尾不会追加分隔线。

如默认报告目录不可写，可以指定其他目录：

```powershell
.\run_text2sql.ps1 -Limit 1 -RunName smoke -OutputRoot C:\temp\ht-eval
```

## 8. 安全与评测口径

- 只接受单条 `SELECT` 或只读 `WITH` 查询；
- 拒绝 DML、DDL、`COPY`、`CALL`、`DO`、`SELECT INTO` 和多语句；
- 数据库连接必须为只读模式；
- 每道题生成失败不会丢失其他结果；
- 部分题失败时仍会评测已有结果，缺失预测按0分处理；
- 第3、5、7题的标准查询当前返回空集，报告时仍需单独关注非空 EX 覆盖率。

Spider/BIRD 的代码和历史自检结果继续保留在 `workspace/standard`，但它们不属于本启动脚本的运行流程。
