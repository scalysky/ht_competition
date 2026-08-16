# SQL 生成模块说明

本目录保留早期的模型 SQL 生成代码，但它已经不属于根目录一键评测脚本的流程。

当前统一入口是仓库根目录的 `run_text2sql.ps1`。它只读取用户提供的 JSON 或 TXT
答案文件，然后计算 EM、EX、R-VES：

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_text2sql.ps1 -Predictions C:\path\answers.json -RunName test
```

该入口：

- 不调用模型 API；
- 不读取 `.knowledge` 或其他知识库；
- 不生成 SQL；
- 输入文件地址由 `-Predictions` 指定，不是写死的。

输入格式和完整用法见
[`../competition_eval/README.md`](../competition_eval/README.md)。
