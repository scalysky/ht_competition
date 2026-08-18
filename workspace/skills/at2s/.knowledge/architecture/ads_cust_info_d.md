# ads_cust_info_d — 客户信息表

## 表描述
客户维度快照表，每行一个客户在某一日的基础信息。（来源：用户提供，来自 `表描述.sql` 的 COMMENT）

实测 `data_dt` 仅含 `20260531` 单日，共 500 个客户；`pty_id` 形如 `C` + 15 位数字，`cust_lvl_cd` 取值 1000001~1000006（全部命中 dim_public type 100），`cust_status` 实测仅 `2000001`（正常），`cust_type` 实测仅 `P`，`gender_cd`∈{5000002,5000003}，各码值字段均已与 dim_public 对应类型对齐（数据推测）。

## 字段
| 字段 | 类型 | 含义 | 来源 | 备注 |
|---|---|---|---|---|
| data_dt | varchar(8) | 日期 | 用户提供 | 字符型 YYYYMMDD，实测仅 20260531 |
| pty_id | varchar(32) | 客户号 | 用户提供 | 形如 C+15位数字，跨表关联主键 |
| sor_pty_id | varchar(32) | 经纪客户号 | 用户提供 | |
| cust_lvl_cd | varchar(12) | 客户等级 | 用户提供 | → dim_public(code_type 100) |
| cust_status | varchar(12) | 账户状态 | 用户提供 | → dim_public(code_type 200) |
| cust_type | varchar(1) | 客户类型 | 用户提供 | 实测仅 `P`，推测 P=个人客户（数据推测） |
| prov_name | varchar(50) | 省份 | 用户提供 | |
| city_name | varchar(50) | 城市 | 用户提供 | |
| birth_dt | varchar(8) | 出生日期 | 用户提供 | 字符型 YYYYMMDD |
| cust_age | numeric(20,0) | 年龄 | 用户提供 | |
| name | varchar(40) | 姓名 | 用户提供 | |
| gender_cd | varchar(12) | 性别代码 | 用户提供 | → dim_public(code_type 500) |
| edu_cd | varchar(32) | 学历代码 | 用户提供 | → dim_public(code_type 600) |
| prof_cd | varchar(100) | 职业类型编码 | 用户提供 | → dim_public(code_type 700) |
| org_id | varchar(100) | 所属营业部ID | 用户提供 | → dim_branch.org_id |

## 关系
- `pty_id` ↔ `dws_cust_aset_d` / `dws_cust_fin_d` / `dwd_cust_hold_d` / `dwd_cust_tran_d` 的 `pty_id`（关系状态：推测，字段名与取值形态一致）。
- 码值字段 `cust_lvl_cd`/`cust_status`/`gender_cd`/`edu_cd`/`prof_cd` → `dim_public.code`（需带 `code_type_id` 过滤）（关系状态：推测，已抽样验证命中）。
- `org_id` → `dim_branch.org_id`（关系状态：推测）。

## 待确认
- `cust_type` 的完整枚举与含义（当前仅见 `P`）。
- 码值语义是否一律以 dim_public 为准（建议是）。
