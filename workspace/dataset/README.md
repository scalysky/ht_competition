# 本地基准数据集

基准数据不提交到 Git。下载和解压后的内容包含数 GB 的压缩包及数据库文件，
超过 GitHub 普通仓库的文件大小和容量限制。

本地目录结构应为：

```text
workspace/dataset/
├─ spider/
│  ├─ spider_data/
│  └─ test_suite/
│     ├─ testsuitedatabases.zip
│     └─ database/
└─ bird/
   └─ mini_dev/
      ├─ minidev_0703.zip
      └─ minidev/
         ├─ MINIDEV/
         ├─ MINIDEV_mysql/
         └─ MINIDEV_postgresql/
```

官方下载地址：

- Spider 1.0：https://yale-lily.github.io/spider
- Spider Test Suite Accuracy 数据库：https://github.com/taoyds/test-suite-sql-eval
- BIRD Mini-Dev：https://github.com/bird-bench/mini_dev

2026-08-11 本地校验结果：

- Spider Test Suite 压缩包通过 CRC 校验，共解压出 3,194 个 SQLite 测试实例。
- BIRD Mini-Dev 压缩包通过 CRC 校验，11 个 SQLite 数据库全部通过
  `PRAGMA quick_check`。
- BIRD Mini-Dev 的 SQLite、MySQL 和 PostgreSQL 三种版本各包含 500 条记录。
