# dwd_cust_tran_d

## 表描述

客户交易类买卖日事实（用户描述）。数据范围 20260105–20260331，共 39,060 行（数据推测）。

**粒度警告**：(data_dt, pty_id, prdt_id, sys_source, ccy) 上存在 595 组重复行（已验证）——同一键下可出现多条买卖批次（如一条仅买入、一条仅卖出，或多条不同数量的买入）。本表实际粒度细于"客户×产品×日"，聚合时必须 SUM，不能假定一键一行（数据推测）。

## 字段

| 字段 | 类型 | 含义 | 来源 |
|---|---|---|---|
| data_dt | varchar(8) | 日期，yyyymmdd 字符串；范围 20260105–20260331 | 用户描述（范围与格式为数据推测） |
| pty_id | varchar(32) | 客户号，与 ads_cust_info_d.pty_id 同格式（385/500 客户有交易记录） | 用户描述（关联验证为数据推测） |
| prdt_id | varchar(12) | 产品ID，与 dim_product.prdt_id 关联（3,127 个产品全部命中） | 用户描述（关联验证为数据推测） |
| sys_source | varchar(20) | 系统来源：普通(nm)、信用(fc)；nm 34,183 行、fc 4,877 行 | 用户描述（分布为数据推测） |
| ccy | varchar(12) | 币种：0 人民币、1 美元、2 港币；当前数据仅出现 0（人民币） | 用户描述（分布为数据推测） |
| buy_cnt | integer | 买入次数 | 用户描述 |
| buy_mnt | numeric(20,4) | 买入数量（份额/股数，非金额） | 用户描述（"数量≠金额"为数据推测） |
| buy_rake | numeric(20,4) | 买入佣金 | 用户描述 |
| buy_amt | numeric(20,4) | 买入金额 | 用户描述 |
| buy_fare | numeric(20,4) | 买入费用 | 用户描述 |
| sell_cnt | integer | 卖出次数 | 用户描述 |
| sell_mnt | numeric(20,4) | 卖出数量（份额/股数，非金额） | 用户描述（"数量≠金额"为数据推测） |
| sell_rake | numeric(20,4) | 卖出佣金 | 用户描述 |
| sell_amt | numeric(20,4) | 卖出金额 | 用户描述 |
| sell_fare | numeric(20,4) | 卖出费用 | 用户描述 |

## 待确认

- rake（佣金）与 fare（费用）的口径区别？总交易成本 = rake + fare 吗？
- 重复行的成因：是否为逐笔委托批次？统计"交易笔数"应使用 SUM(buy_cnt)+SUM(sell_cnt) 还是 COUNT(*)？
