# Text-to-SQL 知识库双模式设计

## 目标

为比赛 PostgreSQL 一键生成与评测脚本增加两种可对比的知识库模式：默认读取完整知识库，或显式关闭知识库。运行时必须在终端和产物元数据中清楚标记实际模式，避免把不同实验条件混在一起。

## 命令行接口

PowerShell 入口新增参数：

```text
-KnowledgeMode Full|None
```

- 默认值为 `Full`，保持普通使用方式简洁。
- `Full`：读取 `workspace/skills/at2s/.knowledge/` 下所有 `.md` 文件。
- `None`：不读取、也不向模型发送任何 `.knowledge` 内容。
- 不保留“只读 correlation.md”的第三种模式。

推荐为两种模式使用不同运行名：

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Full -RunName baseline_full_kb
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Full -RunName baseline_no_kb -KnowledgeMode None
```

## 完整知识库加载

`Full` 模式递归读取 `.knowledge` 下所有 Markdown 文件，包括当前的八个单表说明、`correlation.md`，以及未来可能增加的 `conventions` 和 `troubleshooting` 文档。

加载规则：

1. 只读取扩展名为 `.md` 的文本文件，不读取 `SKILL.md`、数据库访问配置或其它文件。
2. 按相对路径排序，保证同一批文件形成稳定提示词和稳定检查点指纹。
3. 每段内容前标注相对路径，便于模型区分来源，也便于问题定位。
4. 目录不存在、没有 Markdown 文件或所有文件均为空时终止生成，避免把 `Full` 静默降级成 `None`。

## 无知识库模式

`None` 模式只向模型提供：

- 比赛题目；
- PostgreSQL `public` schema 的实时元数据；
- 固定的只读 SQL 生成约束。

该模式不得读取 `.knowledge`，提示词中不得出现知识库正文或知识文件路径。

## 运行标识与产物

生成开始前在终端打印：

```text
知识库模式: Full（已加载 N 个文件）
```

或：

```text
知识库模式: None（未使用知识库）
```

`Full` 模式同时逐行打印加载文件的相对路径。生成阶段输出一个运行元数据文件，至少记录模式、知识文件列表、模型名和生成时间；评测报告继续记录 EM、EX、R-VES，不改变评分算法。

检查点指纹继续基于最终提示上下文计算，因此知识库模式或知识文件内容发生变化时，不会错误复用旧预测。README 要求不同实验使用不同 `RunName`，便于人工识别。

## 兼容性和安全

- 继续使用 OpenAI 兼容 `/chat/completions` 接口，包括 DeepSeek V4 Flash。
- 数据库仍必须处于只读模式。
- 标准 SQL 不发送给模型。
- `.env`、API Key 和数据库密码不写入知识库、日志或运行元数据。
- 旧的 `baseline` 产物属于“仅 correlation.md”的历史结果，不视为新的 `Full` 模式结果。

## 测试和验收

自动化测试至少覆盖：

1. 默认模式为 `Full`。
2. `Full` 递归、排序并合并全部 Markdown 文件。
3. `Full` 在知识库缺失或为空时明确失败。
4. `None` 不访问知识库路径，最终提示词不含知识内容。
5. 启动脚本正确转发模式并在终端打印模式。
6. 两种模式产生不同检查点指纹。
7. 现有模型调用、断点续跑、只读 SQL 校验和 EM/EX/R-VES 测试继续通过。

最终交付包括中文队友操作说明，分别给出 CMD 和 PowerShell 的单题、全量、续跑及仅评测命令。
