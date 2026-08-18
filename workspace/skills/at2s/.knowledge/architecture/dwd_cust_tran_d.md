# dwd_cust_tran_d — 客户交易类买卖日事实

## 表描述
客户买卖交易按"客户号 + 产品 + 日期 + 系统来源 + 币种"的每日事实表，记录买入/卖出的次数、数量、金额、佣金、费用。（来源：用户提供，来自 `表描述.sql` 的 COMMENT）

实测 `data_dt` 范围 `20260105`~`20260331`，共 385 个客户；`sys_source`∈{nm,fc}，`ccy`∈{0,1,2}。样例：`buy_cnt=2, buy_mnt=10000, buy_amt=34100, buy_rake=11.93, buy_fare=0.34`。

## 字段
| 字段 | 类型 | 含义 | 来源 | 备注 |
|---|---|---|---|---|
| data_dt | varchar(8) | 日期 | 用户提供 | 字符型 YYYYMMDD |
| pty_id | varchar(32) | 客户号 | 用户提供 | 关联 ads 等表 |
| prdt_id | varchar(12) | 产品ID | 用户提供 | → dim_product.prdt_id |
| sys_source | varchar(20) | 系统来源：普通(nm)、信用(fc) | 用户提供 | 独立枚举 |
| ccy | varchar(12) | 币种 | 用户提供 | 0 人民币；1 美元；2 港币 |
| buy_cnt | integer | 买入次数 | 用户提供 | |
| buy_mnt | numeric(20,4) | 买入数量 | 用户提供 | |
| buy_rake | numeric(20,4) | 买入佣金 | 用户提供 | |
| buy_amt | numeric(20,4) | 买入金额 | 用户提供 | |
| buy_fare | numeric(20,4) | 买入费用 | 用户提供 | |
| sell_cnt | integer | 卖出次数 | 用户提供 | |
| sell_mnt | numeric(20,4) | 卖出数量 | 用户提供 | |
| sell_rake | numeric(20,4) | 卖出佣金 | 用户提供 | |
| sell_amt | numeric(20,4) | 卖出金额 | 用户提供 | |
| sell_fare | numeric(20,4) | 卖出费用 | 用户提供 | |

## 关系
- `pty_id` ↔ `ads_cust_info_d` / 各事实表（关系状态：推测）。
- `prdt_id` ↔ `dim_product.prdt_id`（关系状态：推测）。
- 与 `dwd_cust_hold_d` 同粒度（客户+产品+日期+来源+币种），可通过全部键关联（关系状态：推测）。

## 待确认
- `buy_mnt`/`sell_mnt`（数量）与 `buy_amt`/`sell_amt`（金额）的单位及与 `mkt_val` 的对应关系。
