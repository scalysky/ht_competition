# 比赛 Text-to-SQL 一键生成与评测

该工具只处理比赛 PostgreSQL 业务题，不调用模型运行 Spider 或 BIRD。它会把比赛题目和实时数据库表结构发送给 OpenAI 兼容模型，逐题生成 SQL，然后调用现有评分器计算 EM、EX 和 R-VES。可以选择默认的完整知识库模式，或完全不读取知识库的对照模式。

模型不会收到 `gold_queries.json` 中的标准 SQL。正式生成期间，评分结果也不会反馈给模型。

## 1. 准备环境

需要：

- Python 3.9 或更高版本；
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

使用 DeepSeek V4 Flash 时填写：

```dotenv
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=替换为真实DeepSeek_API_Key
LLM_MODEL=deepseek-v4-flash
LLM_TIMEOUT_SECONDS=180
```

`.env` 已被 Git 忽略，不要把真实 API Key 写入 `.env.example`、命令行或报告。

## 2. 查看帮助

CMD 中请整行执行：

```cmd
cd C:\Code\Fin_tech_match\ht_competition
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Help
```

如果已经在 PowerShell 中，并且本机允许执行脚本，也可以使用 `./run_text2sql.ps1`。CMD 不支持 PowerShell 的反引号换行符，请优先复制本文的一行命令。

PowerShell 用户可以只对当前窗口临时放开脚本限制，然后直接使用脚本入口：

```powershell
Set-ExecutionPolicy -Scope Process Bypass

# 单题：默认完整知识库
.\run_text2sql.ps1 -Limit 1 -RunName smoke_full_kb

# 全量：默认完整知识库；重复执行同一命令即可断点续跑
.\run_text2sql.ps1 -Full -RunName baseline_full_kb

# 全量：完全不读取知识库
.\run_text2sql.ps1 -Full -RunName baseline_no_kb -KnowledgeMode None

# 只生成 / 只评测
.\run_text2sql.ps1 -Full -RunName baseline_no_kb -KnowledgeMode None -GenerateOnly
.\run_text2sql.ps1 -Full -RunName baseline_no_kb -EvaluateOnly
```

## 3. 选择知识库模式

### 完整知识库（默认）

不写 `-KnowledgeMode` 时默认使用 `Full`。程序递归读取
`workspace/skills/at2s/.knowledge/` 下所有非空 Markdown，包括八个单表说明、`correlation.md`，以及未来加入的业务规范和排错记录：

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Limit 1 -RunName smoke_full_kb
```

终端会打印：

```text
知识库模式: Full（已加载 9 个文件）
  - architecture/ads_cust_info_d.md
  - ...
```

### 不使用知识库

显式传入 `-KnowledgeMode None`。此时模型只收到题目、实时 PostgreSQL Schema 和固定的只读 SQL 约束：

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Limit 1 -RunName smoke_no_kb -KnowledgeMode None
```

终端会打印：

```text
知识库模式: None（未使用知识库）
```

两种实验必须使用不同 `RunName`，不要混用检查点。旧的 `baseline` 结果只加载过 `correlation.md`，不属于新的完整知识库结果。

## 4. 先测试一道题

这一步会产生一次真实模型调用费用：

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Limit 1 -RunName smoke_full_kb
```

脚本会自动：

1. 检查 PostgreSQL 连接是否为只读；
2. 读取 `public` schema；
3. 根据 `KnowledgeMode` 加载完整知识库或明确跳过知识库；
4. 调用模型生成第一题 SQL；
5. 保存预测和检查点；
6. 计算该题 EM、EX 和 R-VES；
7. 生成 JSON、CSV 和 Markdown 报告。

## 5. 运行全部比赛题

确认单题结果正常后运行当前全部7题：

完整知识库：

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Full -RunName baseline_full_kb
```

无知识库：

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Full -RunName baseline_no_kb -KnowledgeMode None
```

必须明确传入 `-Limit N` 或 `-Full`，防止误触发批量付费请求。

## 6. 断点续跑

同一个 `RunName` 默认自动读取 `checkpoint.jsonl`。只有题目、schema、提示词和模型都没有变化时，已成功题目才会跳过：

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Full -RunName baseline_full_kb
```

失败题会重新调用，成功题不会重复计费。如果不想复用旧检查点：

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Full -NoResume
```

未指定 `RunName` 时，`-NoResume` 会创建时间戳目录。

## 7. 只生成或只评测

只调用模型生成 SQL：

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Full -RunName baseline_no_kb -KnowledgeMode None -GenerateOnly
```

对已有预测重新评分，不调用模型：

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Full -RunName baseline_no_kb -EvaluateOnly
```

`EvaluateOnly` 不调用模型，也不会重新加载知识库；它只评测该 `RunName` 中已经生成的预测。

## 8. 输出文件

默认目录：

```text
workspace/standard/eval_runs/competition/<RunName>/
├─ checkpoint.jsonl
├─ run_metadata.json
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
- `run_metadata.json`：记录本次使用的模型、知识库模式和知识文件清单，不含密钥；
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

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Limit 1 -RunName smoke_full_kb -OutputRoot C:\temp\ht-eval
```

## 9. 指标解释

- `EM`：生成 SQL 与标准 SQL 的结构化精确匹配；正确的等价写法也可能得到0。
- `EX`：生成 SQL 与标准 SQL 在当前数据库上的执行结果是否一致。
- `R-VES`：只在执行结果正确时衡量相对执行效率。官方奖励分档允许单题超过100，例如 reward 为1.25时得分约111.80；总分是所有题目的平均值。

当前数据存在需要人工复核的弱覆盖：第3、5、7题的标准 SQL 返回零行；第1题虽然聚合查询返回一行，但计数值为0。错误 SQL 可能因为相同的空集或零计数得到 `EX=1`，正式报告不能只看汇总 EX，还要人工检查 SQL 业务口径。

## 10. 安全与评测口径

- 只接受单条 `SELECT` 或只读 `WITH` 查询；
- 拒绝 DML、DDL、`COPY`、`CALL`、`DO`、`SELECT INTO` 和多语句；
- 数据库连接必须为只读模式；
- 每道题生成失败不会丢失其他结果；
- 部分题失败时仍会评测已有结果，缺失预测按0分处理；
- 完整知识库模式只读取 `.knowledge` 下的 Markdown，不读取 `SKILL.md`、数据库密码或 API Key；
- 第1、3、5、7题需要结合人工语义复核，不能把当前数据上的 `EX=1` 直接等同于 SQL 逻辑正确。

Spider/BIRD 的代码和历史自检结果继续保留在 `workspace/standard`，但它们不属于本启动脚本的运行流程。
