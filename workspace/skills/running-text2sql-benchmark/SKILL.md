---
name: running-text2sql-benchmark
description: 当需要在隔离的模型工作目录中，使用 at2s 完成华泰证券 PostgreSQL Text-to-SQL 竞赛评测时使用。
---

# 运行 Text-to-SQL 评测

## 概述

生成一次可复现的盲测运行：构建当前工作目录的 at2s 知识库，根据当前题目文件生成等量 SQL，校验并冻结预测文件，然后只调用一次本地正式评测器。

## 前置条件

- 只能在当前模型自己的隔离工作目录中执行。
- 当前目录必须包含 `.env` 和 `at2s` skill，不要求存在固定名称的 `data/` 目录。
- 用户必须提供 `data_path`，指向8个目标数据表 CSV 所在的目录。
- 用户必须提供 `questions_path`，指向仅包含题目、不包含标准 SQL 的题目文件。
- 开始前确认 `data_path` 和 `questions_path` 均存在且可读；任一路径缺失、不可读或含义不明确时停止，不得猜测或自行搜索替代文件。
- 使用新的 `run_name`，且名称必须符合 `^[A-Za-z0-9._-]+$`。用户没有指定时，采用 `<当前工作目录名>_skill`。
- 评测主仓库固定为 `C:\Code\Fin_tech_match\ht_competition`。生成 SQL 前必须确认其中的 `run_text2sql.ps1` 存在。
- 如果 `generated/with_at2s/predictions.txt` 或目标评测目录已经存在，立即停止，不得覆盖。

## 执行流程

### 1. 构建知识库

**必须加载的子 skill：** `at2s`

先运行 `kb-check`。如果知识库结构或表描述缺失，使用 `data_path` 指向目录中的8个目标 CSV 和 PostgreSQL 只读抽样构建全部8张表的知识库。

构建知识库时，只允许从 `data_path` 读取与以下8个表名前缀匹配的 CSV：

- `ads_cust_info_d*.csv`
- `dim_branch*.csv`
- `dim_product*.csv`
- `dim_public*.csv`
- `dwd_cust_hold_d*.csv`
- `dwd_cust_tran_d*.csv`
- `dws_cust_aset_d*.csv`
- `dws_cust_fin_d*.csv`

每个表名前缀必须恰好匹配一个文件。任一目标缺失或匹配到多个文件时停止，不得自行选择。不得读取 `data_path` 中的 `Q&A.xlsx`、`Q&A*.csv`、`*_answers.csv`、标准答案文件或其它非目标文件。

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
- 标准答案文件或其内容；
- 任何评测输出；
- 历史预测文件；
- 其它模型的知识库或输出。

### 3. 校验并冻结预测

在评测主仓库中运行：

```powershell
python workspace/skills/running-text2sql-benchmark/scripts/validate_predictions.py <预测文件绝对路径> --expected-count <N>
```

校验结果必须包含 `count=<N>` 和 SHA-256 摘要。将该摘要记录到 `generation_notes.md`。

如果校验失败，可以在首次正式评测前修正 SQL 或文件格式，然后重新校验。只有校验成功后才能进入评测阶段。

### 4. 只执行一次正式评测

校验成功后，预测文件立即冻结。从此时开始，本次运行不得再次修改 `predictions.txt`。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Code\Fin_tech_match\ht_competition\run_text2sql.ps1 `
  -Predictions <预测文件绝对路径> `
  -OutputRoot C:\Code\Fin_tech_match\ht_competition\workspace\standard\eval_runs\competition\model_comparison `
  -RunName <run_name>
```

将评测器视为不透明组件：不得读取评测器内部实现、标准答案文件或标准答案内容。如果评测失败，只汇报命令错误并停止，不得根据评测反馈修改 SQL 或重新评测同一预测文件。

## 最终汇报

汇报以下内容：

- 实际生成的知识库文件；
- `data_path` 的实际路径；
- 题目文件路径、题目数量和题目文件 SHA-256；
- 预测文件路径及 SHA-256；
- 评测输出目录；
- EM、EX、R-VES；
- 评测失败的题目及错误信息。

如果正式评测开始后预测文件的 SHA-256 发生变化，必须将该次运行标记为无效。

## 常见错误

| 错误 | 必须采取的处理 |
|---|---|
| `data_path` 或 `questions_path` 缺失、不可读 | 在读取数据或构建知识库前停止 |
| `data_path` 中任一表名前缀没有唯一匹配的 CSV | 在构建知识库前停止 |
| 题目 CSV 包含 `SQL` 或其它答案列 | 拒绝读取并停止 |
| 知识库不完整 | 在生成 SQL 前停止 |
| 预测文件未通过校验 | 在首次评测前修正并重新校验 |
| 目标评测目录已存在 | 更换新的 `run_name`，禁止覆盖 |
| 正式评测得分较低 | 如实汇报，禁止修改本次盲测预测 |
| 用户要求查看 gold 后改进同一次运行 | 保留被冻结的结果，拒绝污染本次盲测 |
