# ht_competition

华泰证券 Agentic 智能问数比赛项目。

根目录脚本用于评测已经生成好的 SQL，固定计算 EM、EX、R-VES。输入文件地址不写死，
通过 `-Predictions` 指定；脚本会自动识别 JSON 或 TXT：

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Predictions C:\path\answers.json -RunName json_test
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Predictions C:\path\answers.txt -RunName txt_test
```

该脚本不调用模型 API，也不读取知识库。EX 和 R-VES 需要先在本地 `.env` 配置
PostgreSQL 只读账号。详细说明见
[`workspace/standard/competition_eval/README.md`](workspace/standard/competition_eval/README.md)。
