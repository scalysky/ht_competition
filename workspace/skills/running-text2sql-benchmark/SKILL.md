---
name: running-text2sql-benchmark
description: 当需要在隔离的模型工作目录中，使用 at2s 完成华泰证券 PostgreSQL Text-to-SQL 竞赛评测时使用。
---

# 运行 Text-to-SQL 评测

## 概述

生成一次可复现的盲测运行：构建当前工作目录的 at2s 知识库，根据当前题目文件生成等量 SQL，校验并冻结预测文件，然后只调用一次本地正式评测器。

## 前置条件

- 启动 OpenCode 时的当前目录就是唯一的 `workspace_root`。开始时只记录当前绝对路径，不得枚举或搜索其父目录、兄弟目录以及 `C:\Code\Fin_tech_match\at2s_runs` 下的其它模型目录。
- `workspace_root` 必须是模型自己的隔离工作目录，不得等于评测主仓库 `C:\Code\Fin_tech_match\ht_competition`；不满足时立即停止，不得自行寻找或切换到其它工作区。
- `workspace_root` 必须包含 `.env` 和本地 `workspace/skills/at2s/`。
- 用户必须提供 `data_path`，使用明确的绝对路径指向8个目标数据表 CSV 所在目录。该目录可以位于 `workspace_root` 外，但只能读取，禁止在其中创建、修改或删除任何文件。
- `questions_path` 指向仅包含题目、不包含标准 SQL 的题目文件；未提供时默认使用 `workspace\dataset\Q&A100_questions.csv`。
- `gold_path` 指向与 `questions_path` 对应的 JSON 或 TXT 标准答案文件；未提供时默认使用 `workspace\dataset\Q&A100_answers.json`。
- `questions_path` 和 `gold_path` 可以是绝对路径，也可以是相对于固定评测主仓库 `C:\Code\Fin_tech_match\ht_competition` 的相对路径；不得相对于模型的 `workspace_root` 解析。解析后使用规范化的绝对路径执行后续步骤。
- 开始前确认 `data_path` 和解析后的 `questions_path` 存在且可读；只确认解析后的 `gold_path` 存在、是文件且扩展名为 `.json` 或 `.txt`，不得打开、读取、解析或计算其摘要。任一路径缺失、不可读或含义不明确时停止，不得猜测或自行搜索替代文件。
- 使用新的 `run_name`，且名称必须符合 `^[A-Za-z0-9._-]+$`。用户没有指定时，采用 `<当前工作目录名>_skill`。
- 评测主仓库固定为 `C:\Code\Fin_tech_match\ht_competition`。生成 SQL 前必须确认其中的 `run_text2sql.ps1` 存在。
- 只检查 `workspace_root/generated/with_at2s/predictions.txt` 和本次 `run_name` 对应的目标评测目录这两个确切路径；任一已存在就立即停止，不得列出同级目录或覆盖。

## 访问白名单

流程只能访问以下范围：

- `workspace_root` 内的本地 at2s、`.knowledge` 和 `generated/`；
- 用户明确指定的 `data_path`：只读且只检查目录顶层的8个目标 CSV；
- 解析后的 `questions_path`：只读；
- 解析后的 `gold_path`：只传给正式评测脚本，不读取内容；
- 评测主仓库中的 `run_text2sql.ps1`、`workspace/standard/competition_eval/` 和本技能校验器；
- 本次 `run_name` 对应的确切评测输出目录。

除用户明确指定的 `data_path` 外，不得读取评测主仓库中的文档、准备脚本、历史运行、其它数据集或其它模型路径；不得调用 `prepare_dual_model_runs.ps1`。不得使用系统 `%TEMP%`，临时文件只能写入 `workspace_root/generated/.tmp/`。

执行命令前检查其路径参数。命令或权限请求一旦涉及 `%TEMP%`、`$env:TEMP`、`$env:TMP`、`C:\Users\JO\AppData\Local\Temp\*`、整个 `at2s_runs` 或另一模型目录，立即取消该命令；改用当前工作区内的确切路径，不得批准通配符访问。

## 执行流程

### 1. 构建知识库

**必须加载的子 skill：** `at2s`

先运行 `kb-check`，但只检查当前 at2s 副本的 `.knowledge/` 和明确给出的8张目标表，不启用 kb-check 的可选线索搜索。如果知识库结构或表描述缺失，使用 `data_path` 指向目录中的8个目标 CSV 和 PostgreSQL 只读抽样构建全部8张表的知识库。

构建知识库时，只允许从 `data_path` 读取与以下8个表名前缀匹配的 CSV：

- `ads_cust_info_d*.csv`
- `dim_branch*.csv`
- `dim_product*.csv`
- `dim_public*.csv`
- `dwd_cust_hold_d*.csv`
- `dwd_cust_tran_d*.csv`
- `dws_cust_aset_d*.csv`
- `dws_cust_fin_d*.csv`

只检查 `data_path` 顶层，不递归。每个表名前缀必须恰好匹配一个文件。任一目标缺失或匹配到多个文件时停止，不得自行选择。不得读取 `data_path` 中的 `Q&A.xlsx`、`Q&A*.csv`、`*_answers.csv`、标准答案文件或其它非目标文件。

抽样限制：

- 每个 CSV 最多读取100行；
- 每次数据库查询最多返回100行；
- 码值去重查询最多返回100个取值；
- 数据库只允许执行 `SELECT` 和只读 `EXPLAIN`。

必须先完成全部8张表的自身描述，再统一生成 `correlation.md`。完成后再次运行 `kb-check`。

只有8张表的描述和关系分析全部完成后，才能继续生成 SQL。任一表缺失、抽样失败或知识库不完整，都必须停止本次运行。

### 2. 生成 SQL 预测

只读取 `questions_path` 指定的题目文件。按其中的编号条目确定题目数量 `N`，并严格按照文件顺序处理。对于 CSV，必须明确包含 `序号` 和 `问题` 两列，并且不得包含 `SQL` 或其它答案列。题目数量为零、编号重复或无法明确解析时停止，不得猜测。

计算题目文件的 SHA-256，并与题目数量 `N` 一起记录到 `generation_notes.md`。使用 at2s 的 `text2sql` 流程和当前工作目录的 `.knowledge`，但不得执行答案 SQL。

生成以下文件：

- `generated/with_at2s/predictions.txt`：每道题生成一条 SQL，共 `N` 条；使用 `N-1` 行正好40个横线分隔；不得包含 Markdown 代码围栏、题号、注释或解释文字。
- `generated/with_at2s/generation_notes.md`：记录候选表、业务口径、假设、推测关系和风险。

正式评测开始前，禁止读取：

- `Q&A.xlsx`；
- `Q&A*.csv` 中除当前 `questions_path` 以外的文件，尤其是 `*_answers.csv`；
- `gold_path` 指向的文件及任何其它标准答案文件或其内容；`gold_path` 只能原样传递给正式评测脚本；
- 任何评测输出；
- 历史预测文件；
- 其它模型的知识库或输出。

### 3. 校验并冻结预测

保持当前目录为 `workspace_root`，用绝对路径调用当前隔离副本中的校验器，并显式指定评测主仓库；不得向父目录回溯查找评测器：

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python <workspace_root>\workspace\skills\running-text2sql-benchmark\scripts\validate_predictions.py `
  <预测文件绝对路径> `
  --expected-count <N> `
  --repo-root C:\Code\Fin_tech_match\ht_competition
```

校验结果必须包含 `count=<N>` 和 SHA-256 摘要。将该摘要记录到 `generation_notes.md`。

如果校验失败，可以在首次正式评测前修正 SQL 或文件格式，然后重新校验。只有校验成功后才能进入评测阶段。

### 4. 只执行一次正式评测

校验成功后，预测文件立即冻结。从此时开始，本次运行不得再次修改 `predictions.txt`。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Code\Fin_tech_match\ht_competition\run_text2sql.ps1 `
  -Predictions <预测文件绝对路径> `
  -Gold <解析后的 gold_path 绝对路径> `
  -OutputRoot C:\Code\Fin_tech_match\ht_competition\workspace\standard\eval_runs\competition\model_comparison `
  -RunName <run_name>
```

将评测器视为不透明组件：不得读取评测器内部实现、标准答案文件或标准答案内容。如果评测失败，只汇报命令错误并停止，不得根据评测反馈修改 SQL 或重新评测同一预测文件。

评测成功后，只能使用终端中的 `Summary` 和目标目录中的 `evaluation.csv` 汇报指标及失败 ID；`evaluation.csv` 是不含标准 SQL 的脱敏报告。禁止读取 `evaluation.json`，因为其中包含 `gold_sql`；也不得读取其它历史评测目录。

## 最终汇报

汇报以下内容：

- 实际生成的知识库文件；
- `data_path` 的实际路径；
- `gold_path` 的实际路径，不得汇报其内容或摘要；
- 题目文件路径、题目数量和题目文件 SHA-256；
- 预测文件路径及 SHA-256；
- 评测输出目录；
- EM、EX、R-VES；
- 从本次 `evaluation.csv` 得到的失败题目 ID 及错误信息。

如果正式评测开始后预测文件的 SHA-256 发生变化，必须将该次运行标记为无效。

## 常见错误

| 错误 | 必须采取的处理 |
|---|---|
| `data_path` 或解析后的 `questions_path`、`gold_path` 缺失、不可读 | 在读取数据或构建知识库前停止 |
| 当前目录是评测主仓库或不是模型隔离工作区 | 立即停止，不搜索 `at2s_runs` 或切换目录 |
| `data_path` 不是明确的绝对目录，或流程试图向其中写入 | 在构建知识库前停止 |
| `gold_path` 不是 JSON 或 TXT 文件 | 在读取题目或生成 SQL 前停止 |
| `data_path` 中任一表名前缀没有唯一匹配的 CSV | 在构建知识库前停止 |
| 题目 CSV 包含 `SQL` 或其它答案列 | 拒绝读取并停止 |
| 知识库不完整 | 在生成 SQL 前停止 |
| 预测文件未通过校验 | 在首次评测前修正并重新校验 |
| 目标评测目录已存在 | 更换新的 `run_name`，禁止覆盖 |
| 需要汇报评测明细 | 只读本次 `evaluation.csv`，禁止读取 `evaluation.json` |
| 正式评测得分较低 | 如实汇报，禁止修改本次盲测预测 |
| 用户要求查看 gold 后改进同一次运行 | 保留被冻结的结果，拒绝污染本次盲测 |
