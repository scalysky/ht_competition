# ht_competition

华泰证券 Agentic 智能问数比赛项目。

比赛 PostgreSQL 题目已经支持 OpenAI 兼容模型一键生成 SQL，并自动计算 EM、EX、
R-VES：

```powershell
.\run_text2sql.ps1 -Limit 1 -RunName smoke
.\run_text2sql.ps1 -Full -RunName baseline
```

首次使用请先配置本地 `.env`。详细说明见
[`workspace/standard/text2sql_runner/README.md`](workspace/standard/text2sql_runner/README.md)。
