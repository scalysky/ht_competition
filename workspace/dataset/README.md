# Local benchmark datasets

Benchmark data is intentionally excluded from Git because the downloaded and
extracted files contain multi-gigabyte archives and database files that exceed
normal GitHub limits.

Expected local layout:

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

Official sources:

- Spider 1.0: https://yale-lily.github.io/spider
- Spider Test Suite Accuracy databases: https://github.com/taoyds/test-suite-sql-eval
- BIRD Mini-Dev: https://github.com/bird-bench/mini_dev

Local verification performed on 2026-08-11:

- Spider Test Suite ZIP passed CRC validation; 3,194 SQLite instances were extracted.
- BIRD Mini-Dev ZIP passed CRC validation; all 11 SQLite databases passed
  `PRAGMA quick_check`.
- BIRD Mini-Dev contains 500 records for each of SQLite, MySQL, and PostgreSQL.
