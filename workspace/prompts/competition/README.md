# Text-to-SQL 模型实验提示词

本目录保存可直接交给模型的实验提示词。推荐使用 `with_at2s/` 下的完整流程提示词：一次完成本模型独立知识库构建、动态数量 SQL 生成、预测校验和一次正式评测。

## 当前文件

```text
competition/
├─ README.md
├─ with_at2s/
│  ├─ dsv4f_full_benchmark.txt
│  └─ minimax_m3_full_benchmark.txt
└─ no_skill/
   └─ 01_generate_sql.txt
```

## 有 Skill 的两模型实验

必须分别从模型自己的隔离工作目录启动 OpenCode：

```powershell
cd C:\Code\Fin_tech_match\at2s_runs\dsv4f
opencode
```

向该会话发送 `with_at2s/dsv4f_full_benchmark.txt`。

```powershell
cd C:\Code\Fin_tech_match\at2s_runs\minimax_m3
opencode
```

向该会话发送 `with_at2s/minimax_m3_full_benchmark.txt`。

不要从 `C:\Code\Fin_tech_match\ht_competition` 启动生成模型。该目录只保存公共 Skill、题目/标准答案和评测器，不是任何模型的知识库工作区。

每个模型工作目录必须独立包含：

```text
.env
opencode.json
workspace/skills/at2s/
workspace/skills/running-text2sql-benchmark/
```

完整流程的本地输出位于当前模型目录：

```text
workspace/skills/at2s/.knowledge/
generated/with_at2s/predictions.txt
generated/with_at2s/generation_notes.md
```

正式评测输出位于：

```text
C:\Code\Fin_tech_match\ht_competition\workspace\standard\eval_runs\competition\model_comparison\<run_name>\
```

`predictions.txt` 或同名评测目录已经存在时，流程会停止而不是覆盖。要做新的独立实验，应使用干净的模型工作目录和新的 `run_name`。

## 参数说明

- `data_path`：使用用户明确给出的绝对路径，可位于模型工作目录外。两个模型可以共享同一份输入 CSV；模型只能读取该目录顶层8个目标文件，不能向其中写入。
- `questions_path`：题目文件，可为 MD、TXT 或 CSV。CSV 必须含 `序号`、`问题` 两列，不能含 `SQL` 或其它答案列。
- `gold_path`：标准答案文件，只支持 JSON 或 TXT。生成模型不得读取其内容；正式评测时通过 `run_text2sql.ps1 -Gold` 原样传入。
- `run_name`：本次评测的唯一名称，只能包含英文字母、数字、点、下划线和横线。

题目数量不写死。模型从 `questions_path` 解析数量 `N`，生成 `N` 条 SQL 和 `N-1` 条40横线分隔线。

## 盲评与路径边界

- 只允许模型访问当前模型工作目录、明确指定的 `data_path` 和 `questions_path`，以及本次评测必需的主仓库固定路径。
- `gold_path` 只能检查文件存在性并传给评测脚本，不能打开、读取、解析或计算摘要。
- 不得访问另一模型目录、`C:\Code\Fin_tech_match\at2s_runs` 的同级目录或历史运行。
- 不得读取 `evaluation.json`，因为其中含 `gold_sql`；评测后只看终端 `Summary` 和本次 `evaluation.csv`。
- 不得使用系统 `%TEMP%`。临时 SQL 只能写到当前模型目录的 `generated/.tmp/`。
- 如果权限窗口请求 `C:\Users\JO\AppData\Local\Temp\*`、另一模型目录或整个 `at2s_runs`，应拒绝并停止检查触发该请求的命令。
- 不运行准备脚本、测试或目录搜索来“寻找”数据、知识库、题目或答案；所有输入均由提示词给出确切路径。

## 无 Skill 基线

`no_skill/01_generate_sql.txt` 是动态题目数量的生成模板。应在物理上不包含 `at2s`、`.knowledge` 和评测结果的独立目录运行。生成会话关闭后，再由人工调用评测脚本；不要让基线生成会话看到标准答案或评分结果。

## Git 注意事项

以下内容只保存在本地，不提交远程：`.env`、`data/`、`workspace/dataset/` 中的题目和标准答案、`.knowledge/`、`generated/`、预测文件和评测输出。
