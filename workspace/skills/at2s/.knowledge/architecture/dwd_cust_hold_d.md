# dwd_cust_hold_d — 客户持有产品日事实

## 表描述
客户持有产品按"客户号 + 产品 + 日期 + 系统来源 + 币种"的每日事实表，记录持仓份额与市值。（来源：用户提供，来自 `表描述.sql` 的 COMMENT）

实测 `data_dt` 范围 `20260101`~`20260331`，共 463 个客户、3755 个产品；`sys_source`∈{nm,fc}，`ccy`∈{0,1,2}。

## 字段
| 字段 | 类型 | 含义 | 来源 | 备注 |
|---|---|---|---|---|
| data_dt | varchar(8) | 日期 | 用户提供 | 字符型 YYYYMMDD |
| pty_id | varchar(32) | 客户号 | 用户提供 | 关联 ads 等表 |
| prdt_id | varchar(12) | 产品ID | 用户提供 | → dim_product.prdt_id |
| sys_source | varchar(20) | 系统来源：普通(nm)、信用(fc) | 用户提供 | 独立枚举 |
| ccy | varchar(12) | 币种 | 用户提供 | 0 人民币；1 美元；2 港币（独立枚举，不在 dim_public） |
| hold_cnt | numeric(20,4) | 持有份额 | 用户提供 | |
| mkt_val | numeric(20,4) | 持有市值 | 用户提供 | |

## 关系
- `pty_id` ↔ `ads_cust_info_d` / 各事实表（关系状态：推测）。
- `prdt_id` ↔ `dim_product.prdt_id`（关系状态：推测）。
- 与 `dws_cust_fin_d`/`dwd_cust_tran_d` 关联需同时带 `sys_source`、`ccy`、`data_dt`（关系状态：推测）。

## 待确认
- `hold_cnt`/`mkt_val` 单位（份额单位、市值币种对应 ccy）。
