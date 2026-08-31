# at2s — 如何将该 skill 加载到全局 skill 中

## 概述

`at2s` 是一个 **Agentic Text2SQL** 技能，面向华泰证券客户营销数据集，将中文自然语言问数转成 SQL，并维护自身知识库。

## 目录结构

```
at2s/
├── SKILL.md                  # 主技能定义（入口）
├── how_to_use.md             # 本文件
├── .knowledge/               # 知识库（运行时生成）
│   ├── architecture/         # 每表一个 .md，表间关系汇总在 correlation.md
│   ├── conventions/          # 别名、黑话等约定
│   └── troubleshooting/      # 疑问与错误记录
└── skills/                   # 六个子流程
    ├── kb-check/SKILL.md     # 知识库完整度检查
    ├── db-access/SKILL.md    # 数据库访问（抽样、结构、分布）
    ├── kb-build/SKILL.md     # 生成知识库
    ├── kb-modify/SKILL.md    # 修改知识库
    ├── kb-refine/SKILL.md    # 完善知识库
    └── text2sql/SKILL.md     # 生成 SQL（日常主路径）
```

## 加载步骤

将该 skill 注册到全局 skill 池，只需做以下两步：

### 1. 复制整个 `at2s/` 目录到目标 harness 的全局 skills 目录下

保持目录结构不变，确保 `SKILL.md` 位于 `at2s/SKILL.md`，子流程位于 `at2s/skills/*/SKILL.md`。

### 2. 在 harness 的全局配置中注册该 skill

在 harness 的全局 skills 配置（如 `settings.json` 或 `skills` 配置项）中添加：

```json
{
  "skills": [
    "...已有 skill...",
    {
      "name": "at2s",
      "path": "<全局 skills 路径>/at2s",
      "entry": "SKILL.md"
    }
  ]
}
```

具体注册方式取决于目标 harness 的配置格式，核心是：**将 `at2s/` 目录的绝对路径（或相对于全局 skills 根目录的相对路径）注册到 harness 的 skill 列表中**。

## 注意事项

- **SQL 方言为 PostgreSQL**，所有产出的 SQL 与内部临时查询均使用 PostgreSQL 语法。
- **首次使用**须先执行 `kb-check` 完整性检查，确认 `.knowledge/` 目录结构、`db-access` 配置、知识库均就绪。
- **`db-access` 是内部子流程**，不对外暴露，由其它子流程调用；它依赖用户配置的查表方式（写入 `skills/db-access/access.md`）。
- **凭据安全**：`db-access` 下的凭据文件与脚本产物应 gitignore，凭据不得写入任何文件、记忆或回显。
- **`.knowledge/` 目录**在首次初始化时由 `kb-check` 和 `kb-build` 自动生成，无需手动创建。
- 该 skill 的子流程之间通过 `skills/*/SKILL.md` 互相引用，加载时需保证整个 `skills/` 目录完整。
