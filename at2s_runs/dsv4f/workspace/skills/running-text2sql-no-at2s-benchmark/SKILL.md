---
name: running-text2sql-no-at2s-benchmark
description: 在隔离模型工作目录中，不使用 at2s 或任何知识库，依靠模型原生能力生成 PostgreSQL Text-to-SQL，校验冻结后执行一次盲评。
---

# 运行无 at2s Text-to-SQL 基线评测

## 实验定义

这是“无 at2s”基线，不是“完全无 Skill”基线。本 Skill 只规定输入隔离、原生 SQL 生成、预测校验和一次正式评测；不得加载任何其它 Skill，不得构建或读取知识库。

## 前置条件

- OpenCode 启动时的当前目录就是唯一的 `workspace_root`。不得枚举、搜索或读取父目录、兄弟目录、整个 `C:\Code\Fin_tech_match\at2s_runs` 或其它模型工作区。
- `workspace_root` 不得等于评测主仓库 `C:\Code\Fin_tech_match\ht_competition`，并且必须包含 `.env` 和当前 Skill 的本地副本。
- 用户必须提供 `data_path`，使用绝对路径指向8个目标表 CSV 所在目录。该目录可以位于 `workspace_root` 外，但只能读取，禁止写入。
- `questions_path` 可以是题目文件或题目目录；未提供时默认使用 `workspace\dataset\Q&A100_questions.csv`。
- `gold_path` 必须是与全部题目顺序一致的 JSON 或 TXT 文件；未提供时默认使用 `workspace\dataset\Q&A100_answers.json`。
- 相对的 `questions_path` 和 `gold_path` 固定相对于评测主仓库解析，不得相对于 `workspace_root` 解析。后续命令统一使用规范化的绝对路径。
- 只确认 `gold_path` 存在、是文件且扩展名为 `.json` 或 `.txt`；禁止打开、读取、解析或计算其摘要。
- `run_name` 必须符合 `^[A-Za-z0-9._-]+$`；未提供时使用 `<当前目录名>_no_at2s`。
- 只检查本次本地输出目录 `workspace_root/generated/no_at2s/<run_name>/` 和中央评测目录 `C:\Code\Fin_tech_match\ht_competition\workspace\standard\eval_runs\competition\model_comparison\<run_name>\`。任一已存在就停止，不得列出同级目录或覆盖。

## 访问边界

只允许访问：

- `workspace_root` 中的 `.env`、当前 Skill、`generated/`；
- 用户明确指定的 `data_path`：仅限顶层8个目标 CSV，只读；
- 解析后的题目文件：只读；
- 解析后的 `gold_path`：只传给正式评测脚本，不读取内容；
- 评测主仓库中的 `run_text2sql.ps1`、`workspace/standard/competition_eval/`；
- 本次 `run_name` 对应的确切评测输出目录。

禁止：

- 加载或调用 at2s、running-text2sql-benchmark 或任何其它 Skill；
- 读取任何 `workspace/skills/at2s/`、`.knowledge`、architecture、correlation、troubleshooting 或知识库缓存；
- 读取 Q&A.xlsx、合并了问题与 SQL 的 Q&A*.csv、答案 CSV、gold 内容、历史 predictions 或任何历史 evaluation；
- 读取其它模型目录；
- 调用准备脚本或测试来寻找输入；
- 使用系统 `%TEMP%`、`$env:TEMP`、`$env:TMP`。临时文件只能写入 `workspace_root/generated/.tmp/`。

命令或权限请求一旦涉及系统临时目录通配符、整个 `at2s_runs` 或另一模型目录，立即取消，不得批准扩大访问范围。

## 执行流程

### 1. 解析题目

`questions_path` 支持：

- 单个 CSV、MD 或 TXT 文件；
- 目录：只检查顶层，不递归，只读取文件名以 `_questions.csv`、`_questions.md` 或 `_questions.txt` 结尾的文件，按文件名升序处理。

目录模式必须排除文件名包含 `answer`、`answers`、`gold`、`sql`、`evaluation` 或 `prediction` 的文件。

CSV 必须包含“序号”和“问题”两列，不得包含“SQL”或其它答案列。同一文件内不得有空题或重复编号；不同文件可以各自从序号1开始。MD/TXT 必须有明确编号。

按文件顺序和文件内顺序确定题目总数 `N`。若没有题目、格式不明确或发现答案列，立即停止。计算每个题目文件的 SHA-256，在 `generation_notes.md` 中记录绝对路径、摘要、题目数、处理顺序和总数 `N`。

### 2. 只读认识数据

只检查 `data_path` 顶层与以下前缀唯一匹配的 CSV：

- `ads_cust_info_d*.csv`
- `dim_branch*.csv`
- `dim_product*.csv`
- `dim_public*.csv`
- `dwd_cust_hold_d*.csv`
- `dwd_cust_tran_d*.csv`
- `dws_cust_aset_d*.csv`
- `dws_cust_fin_d*.csv`

任一前缀缺失或匹配多个文件时停止。每个 CSV 最多读取100行，不得读取同目录的其它文件。

可使用当前 Skill 自带的 `scripts/psql_ro.ps1`，从 `workspace_root/.env` 读取 PostgreSQL 连接参数，查询 public schema、字段类型、每表最多100行样例和码值字段最多100个去重值。只允许 `SELECT` 和只读 `EXPLAIN`，必须设置超时；禁止执行生成的答案 SQL。

这些观察只用于当前生成过程，不得创建 `.knowledge`、architecture、correlation、troubleshooting 或可供后续运行复用的知识库文件。

### 3. 使用模型原生能力生成 SQL

不要向用户提问。遇到业务口径不明确时采用最合理解释继续生成，并把假设写入说明文件。

生成：

- `generated/no_at2s/<run_name>/predictions.txt`：共 `N` 条 PostgreSQL `SELECT` 或 `WITH ... SELECT`，使用 `N-1` 行正好40个横线分隔。
- `generated/no_at2s/<run_name>/generation_notes.md`：记录题目来源、数据观察、候选表、业务口径、假设和风险。

`predictions.txt` 只能包含 SQL 和分隔线，不得包含题号、文件名、解释、注释或 Markdown 代码围栏；文件开头和结尾不得放分隔线。

### 4. 校验并冻结

保持当前目录为 `workspace_root`，调用当前 Skill 自己的校验器：

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python <workspace_root>\workspace\skills\running-text2sql-no-at2s-benchmark\scripts\validate_predictions.py `
  <predictions.txt 绝对路径> `
  --expected-count <N> `
  --repo-root C:\Code\Fin_tech_match\ht_competition
```

校验必须成功并输出 `count=<N>` 和 SHA-256。将摘要写入 `generation_notes.md`。

首次正式评测前可以修正 SQL 或封装格式并重新校验。校验成功后立即冻结 `predictions.txt`；之后不得再修改。

### 5. 只执行一次正式评测

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Code\Fin_tech_match\ht_competition\run_text2sql.ps1 `
  -Predictions <predictions.txt 绝对路径> `
  -Gold <解析后的 gold_path 绝对路径> `
  -OutputRoot C:\Code\Fin_tech_match\ht_competition\workspace\standard\eval_runs\competition\model_comparison `
  -RunName <run_name>
```

评测器是不透明组件。不得读取其实现、`gold_path` 内容或 `evaluation.json`。评测失败时只汇报命令错误并停止；不得根据反馈修改预测或重新评测同一运行。

评测成功后只能使用终端 `Summary` 和本次 `evaluation.csv` 汇报 EM、EX、R-VES、失败题目 ID 和错误信息。不得读取其它评测目录。

## 最终汇报

汇报：

- 这是无 at2s、但使用流程 Skill 的基线；
- `data_path`；
- 题目文件、各文件题数、总题数和 SHA-256；
- `gold_path` 的解析后路径，不得汇报内容或摘要；
- 预测文件路径和 SHA-256；
- 评测输出目录；
- EM、EX、R-VES；
- 本次 `evaluation.csv` 中的失败 ID 和错误信息。

若冻结后预测文件摘要发生变化，必须将本次运行标记为无效。
