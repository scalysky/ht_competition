# dim_branch — 营业部表

## 表描述
记录营业部及其上级分公司/营业部的层级关系，是一张带快照日期的维度表。（来源：用户提供，来自 `表描述.sql` 的 COMMENT）

实测 `data_dt` 仅含 `20260531` 单日快照；`org_id` 形如 `XX00000001`，`up_org_id` 形如 `XX00000112`（分公司）。共 312 个营业部（数据推测）。

> 注意：`表描述.sql` 的 COMMENT 存在笔误——把 `up_org_id`/`up_org_name` 的注释也写成了 `org_id`/`org_name`。以实际列名为准：第 4、5 列是 `up_org_id`（上级 ID）、`up_org_name`（上级名称）。

## 字段
| 字段 | 类型 | 含义 | 来源 | 备注 |
|---|---|---|---|---|
| data_dt | varchar(8) | 日期 | 用户提供 | 字符型 YYYYMMDD，实测仅 20260531 |
| org_id | varchar(50) | 营业部ID | 用户提供 | 与 `ads_cust_info_d.org_id` 关联 |
| org_name | varchar(100) | 营业部名称 | 用户提供 | |
| up_org_id | varchar(50) | 上级营业部/分公司ID | 用户提供 | 自关联 `org_id` 形成层级 |
| up_org_name | varchar(100) | 上级营业部/分公司名称 | 用户提供 | |

## 关系
- `org_id` 自关联 `up_org_id`：营业部 → 分公司（关系状态：推测）。
- `ads_cust_info_d.org_id` → `org_id`（ads 实际出现 28 个营业部，为 dim_branch 的子集）。

## 待确认
- 层级是否仅两级（营业部→分公司），是否存在更上层（如大区）。
