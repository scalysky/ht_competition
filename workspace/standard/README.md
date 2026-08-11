# Text-to-SQL 评测工具

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
