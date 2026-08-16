# dws_cust_fin_d — 客户资金流动日事实

## 表描述

客户资金流动日事实表，4892 行，覆盖 **56 个日期 `20260105`–`20260331`**（比 aset/hold 的 90 天短，起日晚 4 天），粒度 `(data_dt, pty_id, sys_source)` 唯一。（来源：数据推测）

仅 370 名普通(nm)客户 + 48 名信用(fc)客户有资金流水——**不是每位客户每天都有行**，跨客户比较时注意空值即无流水。（来源：数据推测）

## 字段

| 字段 | 类型 | 说明 | 来源 |
|---|---|---|---|
| data_dt | varchar(8) | 日期，`YYYYMMDD` 字符串 | 用户提供 |
| pty_id | varchar(32) | 客户号 | 用户提供 |
| sys_source | varchar(20) | 系统来源：普通(nm)、信用(fc) | 用户提供 |
| cash_in | numeric(20,4) | 现金转入 | 用户提供 |
| cash_out | numeric(20,4) | 现金转出 | 用户提供 |
| tran_in | numeric(20,4) | 证券转入、托管转入、转托转入 | 用户提供 |
| tran_out | numeric(20,4) | 证券转出、托管转出、转托转出 | 用户提供 |
| assign_in | numeric(20,4) | 指定转入 | 用户提供 |
| assign_out | numeric(20,4) | 撤指定转出 | 用户提供 |
