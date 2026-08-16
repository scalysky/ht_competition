# dws_cust_fin_d

## 表描述

客户资金流动日事实（用户描述）。每客户每日每系统一行，粒度 (data_dt, pty_id, sys_source) 唯一（已验证无重复）——同一客户同一天最多有 nm、fc 两行。数据范围 20260105–20260331，共 4,892 行（数据推测）。

## 字段

| 字段 | 类型 | 含义 | 来源 |
|---|---|---|---|
| data_dt | varchar(8) | 日期，yyyymmdd 字符串；范围 20260105–20260331 | 用户描述（范围与格式为数据推测） |
| pty_id | varchar(32) | 客户号，与 ads_cust_info_d.pty_id 同格式（380/500 客户有资金流水） | 用户描述（关联验证为数据推测） |
| sys_source | varchar(20) | 系统来源：普通(nm)、信用(fc)；nm 3,733 行、fc 1,159 行 | 用户描述（分布为数据推测） |
| cash_in | numeric(20,4) | 现金转入 | 用户描述 |
| cash_out | numeric(20,4) | 现金转出 | 用户描述 |
| tran_in | numeric(20,4) | 证券转入、托管转入、转托转入 | 用户描述 |
| tran_out | numeric(20,4) | 证券转出、托管转出、转托转出 | 用户描述 |
| assign_in | numeric(20,4) | 指定转入 | 用户描述 |
| assign_out | numeric(20,4) | 撤指定转出 | 用户描述 |

## 待确认

- "净流入"口径：是 cash_in - cash_out（仅现金），还是全部 in/out 字段合计？tran_in/assign_in 是否计入资金流入？
