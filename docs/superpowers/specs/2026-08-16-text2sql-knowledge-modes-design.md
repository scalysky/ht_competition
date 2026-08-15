# Text-to-SQL 知识库双模式设计

## 目标

一键脚本支持两种可对比的运行方式，并在终端和运行元数据中明确记录实际模式。

## 两种模式

参数为 `-KnowledgeMode Full|None`，默认 `Full`。

- `Full`：读取 `workspace/skills/at2s/.knowledge/` 下全部非空 Markdown。
- `None`：完全不读取知识库，只向模型提供题目、实时 PostgreSQL Schema 和只读 SQL 约束。

两种实验应使用不同的 `RunName`，避免复用检查点。

## 加载规则

- `Full` 按相对路径稳定排序并合并知识文件，包括单表说明、`correlation.md`、业务规范和排错记录。
- 不读取 `SKILL.md`、数据库访问配置或其它文件。
- 拒绝符号链接和知识库目录外的文件。
- 知识库缺失或为空时直接报错，不静默降级。

## 运行标识

终端显示：

```text
知识库模式: Full（已加载 N 个文件）
知识库模式: None（未使用知识库）
```

`run_metadata.json` 记录模式、知识文件列表、模型和生成时间。知识内容变化会改变检查点指纹。

## 安全与验收

- 数据库必须为只读模式，标准 SQL 不发送给模型。
- API Key、数据库密码和 `.env` 内容不得写入日志或产物。
- 测试覆盖默认模式、完整加载、无知识库、路径边界、模式转发和检查点隔离。
- 具体启动命令见 `workspace/standard/text2sql_runner/README.md`。
