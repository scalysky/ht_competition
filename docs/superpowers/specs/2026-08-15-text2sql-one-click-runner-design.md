# Text-to-SQL 一键生成与评测脚本设计

## 目标

提供一个 Windows PowerShell 一键入口，支持 Spider Dev、BIRD Mini-Dev 和比赛 PostgreSQL 三套数据。脚本读取题目与对应数据库结构，通过 OpenAI 兼容接口逐题生成 SQL，实时保存结果，并调用现有评测器输出报告。

第一版不负责训练或微调模型，也不将评测结果反馈给模型。它用于可重复的一次生成基线评测。

## 用户入口

仓库根目录新增 `run_text2sql.ps1`。典型命令如下：

```powershell
.\run_text2sql.ps1 -Dataset spider -Limit 10
.\run_text2sql.ps1 -Dataset bird -Limit 10
.\run_text2sql.ps1 -Dataset competition -Full
```

`-Dataset` 必须是 `spider`、`bird` 或 `competition`。为避免误调用大量模型请求，必须在 `-Limit N` 和 `-Full` 中显式选择一个，二者互斥。

脚本默认执行“生成 + 评测”。另外支持：

- `-GenerateOnly`：只生成预测文件；
- `-EvaluateOnly`：只评测已经存在的预测文件；
- `-Resume`：复用检查点，跳过已经成功生成的题目；默认开启；
- `-NoResume`：从第一题重新生成，并写入新的运行目录。

## 模型配置

模型通过 OpenAI 兼容的非流式 Chat Completions 接口调用。仓库根目录 `.env` 增加：

```dotenv
LLM_BASE_URL=https://example.com/v1
LLM_API_KEY=replace-me
LLM_MODEL=replace-me
LLM_TIMEOUT_SECONDS=120
```

真实密钥只存放于已被 Git 忽略的 `.env`。`.env.example` 只增加变量名和占位值。

第一版使用 Python 标准库发送 HTTP 请求，避免增加 OpenAI SDK 依赖。请求失败、限流或服务端错误最多重试 3 次，并使用短暂递增等待。模型温度固定为 0，以提高基线可重复性。

## 组件划分

新增目录 `workspace/standard/text2sql_runner/`：

- `generate.py`：命令行入口，协调数据读取、提示构造、模型调用、检查点和输出；
- `datasets.py`：将三套数据转换为统一的题目对象，并生成对应 schema 文本；
- `llm_client.py`：加载模型配置并调用 OpenAI 兼容接口；
- `prompts.py`：生成统一系统提示和数据集特定用户提示；
- `outputs.py`：原子写入检查点、评测 JSON 和横线分隔 TXT；
- `tests/`：覆盖数据加载、提示词防泄漏、SQL 清洗、输出格式和断点续跑。

PowerShell 入口只负责参数校验、调用 Python 生成器以及调用已有评测器，不复制 Python 中的数据处理逻辑。

## 统一题目模型

三套数据加载后统一为以下逻辑字段：

```text
id           稳定题号
dataset      spider、bird 或 competition
db_id        所属数据库；比赛固定为 competition
question     自然语言问题
evidence     BIRD 提供的补充知识；其他数据为空
schema       当前 db_id 对应的表、列、主键和外键
```

提示中绝不包含标准 SQL。比赛数据可以从 `gold_queries.json` 读取 `id` 和 `question`，但加载层必须丢弃 `sql` 字段后才能构造提示。

### Spider

- 题目：`workspace/dataset/spider/spider_data/dev.json`
- schema：`workspace/dataset/spider/spider_data/tables.json`
- 每题只发送其 `db_id` 对应的表、字段、主键和外键。
- 输出供官方 Spider 评测器使用的制表符格式预测文件。

### BIRD Mini-Dev

- 题目：`workspace/dataset/bird/mini_dev/minidev/MINIDEV/mini_dev_sqlite.json`
- schema：同目录 `dev_tables.json`
- 提示中包含该题 `evidence`，并只发送当前 `db_id` 的 schema。
- 输出 BIRD 官方评测器所需的带 `db_id` 预测 JSON。

### 比赛 PostgreSQL

- 题目：`workspace/standard/competition_eval/gold_queries.json` 中的 `id` 和 `question`；
- schema：使用现有只读 PostgreSQL 配置读取 `information_schema` 和主外键元数据；
- 模型不得接触 `gold_queries.json` 的 `sql` 内容；
- 输出沿用比赛评分器的 `[{'id': ..., 'sql': ...}]` JSON 格式。

## 提示与 SQL 输出规则

系统提示要求模型：

- 只返回一条 SQL，不解释、不使用 Markdown 代码块；
- 只生成只读 `SELECT` 或 `WITH ... SELECT`；
- 只能使用给定 schema 中存在的表和字段；
- 根据主外键判断 JOIN，不凭空创造关联字段；
- 保持题目要求的聚合、筛选、排序、去重、日期和 NULL 语义；
- Spider/BIRD 使用 SQLite 方言，比赛使用 PostgreSQL 方言。

生成器清除模型偶尔返回的 Markdown 代码围栏和首尾空白，但不改写 SQL 逻辑。多语句或非只读 SQL 记录为失败，不进入有效预测结果。

## 输出与检查点

每次运行使用独立目录：

```text
workspace/standard/eval_runs/<dataset>/<model>/<run_id>/
├─ checkpoint.jsonl
├─ predictions.json
├─ predictions.txt
├─ errors.json
└─ evaluation.*
```

每完成一道题，先以追加方式写入 `checkpoint.jsonl`。最终文件通过临时文件替换方式原子写入，防止进程中断产生半个 JSON。

`predictions.txt` 只包含 SQL，各答案之间严格使用一行 40 个连字符：

```text
SELECT ...
----------------------------------------
SELECT ...
```

文件末尾不额外添加分隔线。`predictions.json` 保留题号和 `db_id`，是评测器的权威输入；TXT 仅用于人工查看或交付。

## 评测编排

生成成功后，PowerShell 根据数据集调用：

- Spider：官方 EM/EX；完整运行时再调用 Test Suite Accuracy；
- BIRD Mini-Dev：官方 EX 和现有 `run_bird_rves.py`；
- 比赛：`competition_eval/evaluate.py` 的 EM、EX、R-VES。

`-Limit` 冒烟测试只评测对应预测子集；如果官方评测器不能直接接受子集，入口先生成对齐的 gold 子集文件。评测结果不传回生成器，也不用于重新生成 SQL。

## 失败处理

- 缺少 `.env` 配置、数据文件或依赖时，在发出模型请求前失败并给出具体路径；
- 接口请求失败最多重试 3 次，仍失败则记录题号、错误类型和消息；
- 某题失败不影响后续题目；最终进程以非零状态提示存在失败；
- `-Resume` 只跳过相同数据集、模型和输入指纹下已经成功的题目；
- schema、题目集或模型发生变化时使用新的输入指纹，防止错误复用旧结果；
- 日志和报告不得打印或保存 API Key、PostgreSQL 密码。

## 测试策略

测试不调用真实模型，也不消耗 API：

1. 使用最小 Spider、BIRD 和比赛 fixture 验证统一题目模型与 schema 格式；
2. 验证比赛提示中不出现标准 SQL；
3. 验证 SQL 代码围栏清理及多语句、写操作拒绝；
4. 验证 TXT 的题目间分隔符恰好为 40 个 `-`，且末尾无分隔符；
5. 验证检查点恢复、输入指纹不匹配和失败记录；
6. 使用假 HTTP 服务验证请求格式、超时和重试，不使用仅验证 mock 调用次数的测试；
7. 使用 `-Limit 1` 进行一次人工许可下的真实接口冒烟测试；
8. 运行现有比赛评分器单元测试，确保没有回归。

## 验收标准

- 三套数据均能通过同一个 PowerShell 入口选择运行；
- 每题只获得其所属数据库 schema，且模型看不到标准 SQL；
- 支持中断恢复，不重复收费调用已成功题目；
- 同时生成评测 JSON 和 40 连字符分隔 TXT；
- 可以自动启动对应的现有评测器并保留报告；
- 密钥不进入 Git、日志或报告；
- 新增测试和现有 competition evaluator 测试全部通过。
