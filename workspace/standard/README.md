# Text-to-SQL 评测工具

## 比赛 SQL 一键生成与评测

仓库根目录的 `run_text2sql.ps1` 可以读取比赛题目和 PostgreSQL schema，通过
OpenAI 兼容接口逐题生成 SQL，并自动计算 EM、EX、R-VES。该入口只处理比赛数据，
不调用模型运行 Spider 或 BIRD。

先运行一道题进行付费冒烟测试：

```powershell
.\run_text2sql.ps1 -Limit 1 -RunName smoke
```

确认后运行当前全部7题：

```powershell
.\run_text2sql.ps1 -Full -RunName baseline
```

模型答案同时保存为评分 JSON 和使用40个 `-` 分隔的 TXT。完整配置、断点续跑和
输出文件说明见 `workspace/standard/text2sql_runner/README.md`。

## 比赛 PostgreSQL 连接

`competition_eval` 包含远程 PostgreSQL 只读连接检查、7 条比赛标准 SQL
和批量执行验证脚本。数据库地址与密码通过仓库根目录的 `.env`
读取，真实密码不提交到 Git。详细命令见
`workspace/standard/competition_eval/README.md`。

已在远程 PostgreSQL 使用标准 SQL 同时作为预测 SQL 完成 7 题 Gold-to-Gold
全指标自检（R-VES 每题预热 1 次、重复 5 次）：

- EM：100.00（7/7）
- EX：100.00（7/7）
- R-VES：96.17
- 第 3、5、7 题的标准结果为空，已在报告中标记为空结果匹配。

R-VES 低于 100 来自官方奖励阈值对 1.0 附近耗时抖动的敏感性，不代表
Gold-to-Gold 的执行结果不一致。

`spider_eval` 以 Git 子模块形式引用 Spider 官方评测器。

克隆仓库时应同时拉取子模块；如果已经完成普通克隆，请执行：

```bash
git submodule update --init --recursive
```

官方评测器依赖 NLTK 及其分词数据：

```bash
python -m pip install nltk
python -m nltk.downloader punkt_tab
```

## Spider Dev 冒烟测试

已使用标准 SQL 同时作为预测 SQL，对 Spider Dev 的全部 1,034 条样本完成
Gold-to-Gold 测试：

- Exact Match：1.000（1,034/1,034）
- Execution Accuracy：0.998（1,032/1,034）

两条 EX 失败记录是 `wta_1` 中内容相同的样本，其查询结果在
`players.last_name` 字段包含非 UTF-8 值。即使预测 SQL 与标准 SQL 完全相同，
Python 默认的 SQLite 文本解码器仍会报错。为保证与官方数据一致，不应直接修改
原始数据库；报告结果时应将这两条记录标注为数据编码异常。

## Spider Test Suite Accuracy 自检

`test_suite_sql_eval` 是 Spider Test Suite Accuracy 官方评测器。本地测试套件数据库
位于 `workspace/dataset/spider/test_suite/database`。

已使用标准 SQL 同时作为预测 SQL，对 Spider Dev 的 1,034 条样本完成测试：

- easy：1.000（248/248）
- medium：1.000（446/446）
- hard：1.000（174/174）
- extra：1.000（166/166）
- 总 Test Suite Accuracy：1.000（1,034/1,034）

## BIRD Mini-Dev SQLite 自检

`bird_mini_dev_eval` 是 BIRD Mini-Dev 官方评测代码。本地数据位于
`workspace/dataset/bird/mini_dev/minidev/MINIDEV`，包含 500 条样本和 11 个
SQLite 数据库；全部数据库均已通过 `PRAGMA quick_check`。

使用标准 SQL 同时作为预测 SQL，在官方默认单条 30 秒超时设置下得到：

- simple：100.00（148 条）
- moderate：99.60（250 条）
- challenging：99.02（102 条）
- 总 Execution Accuracy：99.60（498/500）

未通过的两条并非结果不同，而是 gold SQL 本身执行超时（以下为零基索引）：

- 索引 340，数据库 `codebase_community`
- 索引 393，数据库 `card_games`

将单条超时提高到 120 秒后，这两条仍然超时。原始
`mini_dev_sqlite_gold.sql` 另有 3 行将 SQL 与 `db_id` 之间的制表符误写为空格，
对应的零基索引为 32、498、499（文件第 33、499、500 行）。自检使用
`eval_runs` 中生成的规范化副本，未修改原始数据文件。

### BIRD R-VES 实测

`run_bird_rves.py` 复用 BIRD 官方的 SQL 执行、奖励分档和 R-VES 聚合函数，
默认按 Mini-Dev README 建议重复计时 5 次，超时系数为 3 秒，因此官方实现中的
每题任务级总超时为 15 秒。完整 500 题 Gold-to-Gold 实测结果如下：

- simple：93.53（148 条）
- moderate：91.01（250 条）
- challenging：86.25（102 条）
- 总 R-VES：90.79（500 条）
- 非零奖励：483/500；17 条超时或执行异常分支按官方规则计 0
- 总耗时：241.25 秒（4 个进程）

其中零奖励列表包含 EX 阶段已知的索引 340 和 393。R-VES 衡量正确 SQL 的相对
执行效率，相同 SQL 也会因缓存、计时波动、奖励分档和超时而不等于 100；这不表示
Gold-to-Gold 的查询结果不一致。

Windows 的 `time.time()` 分辨率为 15.625 毫秒，部分极短 SQLite 查询会被测为
0 秒并触发官方比值计算的除零异常。运行入口在 Windows 默认改用
`time.perf_counter()`（本机分辨率为 0.1 微秒），其他评测逻辑保持不变；所用计时源
会写入 JSON 报告。执行命令：

```powershell
$env:PYTHONPATH = "$PWD\workspace\standard\.deps_bird"
python workspace/standard/run_bird_rves.py --num-cpus 4
```

详细结果默认写入以下本地文件；`eval_runs` 是生成目录，不提交到 Git：

- `workspace/standard/eval_runs/bird_mini_dev_rves_gold_selftest.json`
- `workspace/standard/eval_runs/bird_mini_dev_rves_gold_selftest.txt`
