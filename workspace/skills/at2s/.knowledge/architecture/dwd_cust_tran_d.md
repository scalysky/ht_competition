# dwd_cust_tran_d — 客户交易类买卖日事实

## 表描述

客户交易类买卖日事实表，39060 行，覆盖 **56 个日期 `20260105`–`20260331`**（与 fin 同期，比 aset/hold 短）。（来源：数据推测）

**粒度陷阱（重要）**：按 `(data_dt, pty_id, prdt_id, sys_source, ccy)` 五字段去重只得 38461 —— 存在同键多行（同日同客户同产品多笔成交各占一行，如 20260305 客户 C000000000000179 产品 9900295411 有 3 行）。**行数 ≠ 成交笔数：笔数用 `buy_cnt`/`sell_cnt` 求和，金额用对应金额字段 SUM**，绝不可 `COUNT(*)` 当笔数。（来源：数据推测，实测验证）

## 字段

| 字段 | 类型 | 说明 | 来源 |
|---|---|---|---|
| data_dt | varchar(8) | 日期，`YYYYMMDD` 字符串 | 用户提供 |
| pty_id | varchar(32) | 客户号 | 用户提供 |
| prdt_id | varchar(12) | 产品ID，关联 `dim_product` | 用户提供 |
| sys_source | varchar(20) | 系统来源：普通(nm)、信用(fc) | 用户提供 |
| ccy | varchar(12) | 币种：0 人民币、1 美元、2 港币。实测交易几乎全为人民币 | 用户提供 + 数据推测 |
| buy_cnt | integer | 买入次数 | 用户提供 |
| buy_mnt | numeric(20,4) | 买入数量 | 用户提供 |
| buy_rake | numeric(20,4) | 买入佣金 | 用户提供 |
| buy_amt | numeric(20,4) | 买入金额 | 用户提供 |
| buy_fare | numeric(20,4) | 买入费用 | 用户提供 |
| sell_cnt | integer | 卖出次数 | 用户提供 |
| sell_mnt | numeric(20,4) | 卖出数量 | 用户提供 |
| sell_rake | numeric(20,4) | 卖出佣金 | 用户提供 |
| sell_amt | numeric(20,4) | 卖出金额 | 用户提供 |
| sell_fare | numeric(20,4) | 卖出费用 | 用户提供 |
