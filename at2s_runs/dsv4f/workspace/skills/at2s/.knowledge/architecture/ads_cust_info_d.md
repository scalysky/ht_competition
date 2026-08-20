# ads_cust_info_d

## 表描述

- 表的业务含义：客户画像/客户信息主表（ADS 应用层），保存个人客户的档案级属性信息，是客户营销场景的客户主维表。
- 数据粒度：一行 = 一个客户（`pty_id`）在某一个数据日期（`data_dt`）的档案快照。同一客户同一日期只应有一行。
- 每行代表什么：一名自然人客户的营销档案记录，包括客户等级、状态、类型、地区、年龄、姓名（脱敏）、性别、学历、职业及归属营业部。
- 可能的主键或唯一键：`(data_dt, pty_id)`。抽样中 `data_dt` 唯一值为 `20260531`，`pty_id` 与 `sor_pty_id` 均唯一。
- 日期字段和时间范围：`data_dt`（字符型 8 位，格式 YYYYMMDD）为数据日期，当前库内仅 `20260531` 一个日期（500 行）；`birth_dt` 为出生日期（字符型 8 位）。注意：该表的快照日期（20260531）晚于各事实表（dwd/dws）的时间范围（20260101–20260331），与事实表在 `data_dt` 上无交集，不宜用 `data_dt` 关联事实表。
- 适合回答的业务问题：客户在哪里（地区、营业部）、客户的等级/状态/类型分布、客户的年龄/性别/学历/职业画像、按营业部或地区统计客户构成等。
- 使用时需要注意的限制：`name` 已脱敏（示例形如 `伟***`、`文***`），只能用于人数统计不能用于识别；`cust_type` 抽样中全部为 `P`（个人）；`prov_name`/`city_name` 为文字值，存在“北京市/北京市”这种省市同名的写法；`cust_age` 为数值型整数。

## 字段

| 字段名 | 数据类型 | 字段说明 | 示例或码值 | 来源 |
|---|---|---|---|---|
| data_dt | character varying(8) | 数据日期，YYYYMMDD | 20260531 | 用户提供 |
| pty_id | character varying(32) | 客户号（内部统一客户标识），`C`+15位数字 | C000000000000024 | 用户提供 |
| sor_pty_id | character varying(32) | 源系统客户号，与 `pty_id` 存在转换关系（`pty_id = 'C' || substr(sor_pty_id,5)`，已抽样验证 500/500） | 6666000000000000024 | 数据推测（转换关系已抽样验证，但业务含义未人工确认） |
| cust_lvl_cd | character varying(12) | 客户等级码（码表 dim_public code_type_id=100），1000001–1000006 | 1000003 | 数据推测 |
| cust_status | character varying(12) | 客户状态码（码表 dim_public code_type_id=200），抽样见 2000001/2000004/2000005 | 2000001 | 数据推测 |
| cust_type | character varying(1) | 客户类型码，抽样全部为 P | P | 数据推测 |
| prov_name | character varying(50) | 客户所属省/直辖市名称 | 江苏省 | 用户提供 |
| city_name | character varying(50) | 客户所属市名称 | 苏州市 | 用户提供 |
| birth_dt | character varying(8) | 出生日期，YYYYMMDD | 19761104 | 用户提供 |
| cust_age | numeric(20,0) | 客户年龄（整数） | 49 | 用户提供 |
| name | character varying(40) | 客户姓名（已脱敏，含 `*`） | 伟*** | 用户提供 |
| gender_cd | character varying(12) | 性别码（码表 dim_public code_type_id=500）：5000002=男，5000003=女 | 5000003 | 数据推测 |
| edu_cd | character varying(32) | 学历码（码表 dim_public code_type_id=600），抽样见 6000003–6000009 | 6000005 | 数据推测 |
| prof_cd | character varying(100) | 职业码（码表 dim_public code_type_id=700），抽样见 7000001–7000058 | 7000031 | 数据推测 |
| org_id | character varying(100) | 客户归属营业部机构号（关联 dim_branch.org_id，抽样验证 0 缺失） | XX00000054 | 数据推测 |

## 数据特征

- 抽样中发现的主要取值特征：全部为个人客户（cust_type=P）；prov_name 多为“江苏省”，city_name 多为“苏州市”，另有“北京市/北京市”、“云南省/昆明市”等；`name` 全部含 `*` 脱敏。
- 空值情况：`birth_dt` 无空值；其余字段抽样未发现空值（含非空约束的 dim 表另查）。
- 码值字段：`cust_lvl_cd`（1000001–1000006，6 个值）、`cust_status`（2000001 正常、2000004 销户、2000005 休眠已确认，共 3 个值）、`cust_type`（P）、`gender_cd`（5000002/5000003）、`edu_cd`（6000003–6000009，7 个值）、`prof_cd`（31 个值，7000001–7000058）。上述码值均可通过 dim_public.code 关联 dim_public.describe 得到中文含义。
- 金额和数量字段：无（本表为属性表）。
- 日期字段：`data_dt` 库内仅一个值 20260531；`birth_dt` 为出生日期（YYYYMMDD）。
- 客户、产品、机构等标识字段：`pty_id` 客户标识（与全部 dwd/dws 表的 pty_id 匹配，抽样验证 0 缺失）；`sor_pty_id` 源客户号（与 pty_id 有转换关系）；`org_id` 营业部标识（关联 dim_branch）。
- 可能影响聚合或关联的粒度问题：一行一客户一日期；快照日期与事实表日期区间无交集，与事实表关联只能按 `pty_id`（并注意事实表可能按天多行）。

## 待确认

- `cust_lvl_cd` 各码值对应的等级名称（钻石卡/白金卡/金卡/银卡/理财卡/空），虽 dim_public 有 describe，但 1000006=空 的语义需人工确认。
- `cust_status` 业务口径（2000001=正常、2000004=销户、2000005=休眠已确认），建议人工确认。
- `cust_type` 仅出现 P，其它取值（如机构客户 C 等）是否存在未知。
- `sor_pty_id` 的业务来源系统含义未人工确认（转换关系已抽样验证）。
- 主键 `(data_dt, pty_id)` 未经索引/约束确认（information_schema 未显示约束，需人工确认）。
- 表中仅一个 data_dt，是否在其它日期有历史快照未知。
