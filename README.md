# ht_competition

华泰证券 Agentic 智能问数比赛项目。

比赛 PostgreSQL 题目已经支持 OpenAI 兼容模型一键生成 SQL，并自动计算 EM、EX、
R-VES。默认加载完整业务知识库：

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Limit 1 -RunName smoke_full_kb
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Full -RunName baseline_full_kb
```

完全不读取知识库的对照实验：

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Full -RunName baseline_no_kb -KnowledgeMode None
```

首次使用请先配置本地 `.env`。详细说明见
[`workspace/standard/text2sql_runner/README.md`](workspace/standard/text2sql_runner/README.md)。
