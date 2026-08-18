# dws_cust_fin_d — 客户资金流动日事实

## 表描述
客户资金流动按"客户号 + 日期 + 系统来源"的每日事实表，记录现金/证券/指定等各类资金进出。（来源：用户提供，来自 `表描述.sql` 的 COMMENT）

实测 `data_dt` 范围 `20260101`~`20260331`；`sys_source` 取值 `nm`（普通）、`fc`（信用）。

## 字段
| 字段 | 类型 | 含义 | 来源 | 备注 |
|---|---|---|---|---|
| data_dt | varchar(8) | 日期 | 用户提供 | 字符型 YYYYMMDD |
| pty_id | varchar(32) | 客户号 | 用户提供 | 关联 ads 等表 |
| sys_source | varchar(20) | 系统来源：普通(nm)、信用(fc) | 用户提供 | 独立枚举，不在 dim_public |
| cash_in | numeric(20,4) | 现金转入 | 用户提供 | |
| cash_out | numeric(20,4) | 现金转出 | 用户提供 | |
| tran_in | numeric(20,4) | 证券转入、托管转入、转托转入 | 用户提供 | |
| tran_out | numeric(20,4) | 证券转出、托管转出、转托转出 | 用户提供 | |
| assign_in | numeric(20,4) | 指定转入 | 用户提供 | |
| assign_out | numeric(20,4) | 撤指定转出 | 用户提供 | |

## 关系
- `pty_id` ↔ `ads_cust_info_d` / `dws_cust_aset_d` / `dwd_cust_hold_d` / `dwd_cust_tran_d`（关系状态：推测）。
- 与 `dwd_cust_hold_d`/`dwd_cust_tran_d` 关联需同时带 `sys_source` 才能对齐账户口径（关系状态：推测）。

## 待确认
- 各金额字段单位/币种（无 ccy，推测人民币元）。
