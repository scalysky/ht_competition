# dwd_cust_hold_d

## 表描述

- 表的业务含义：客户持仓明细事实表（DWD 层），记录每个客户在每个数据日期对每只产品的持仓数量与市值（按产品、系统来源、币种展开）。
- 数据粒度：一行 = 一个客户（`pty_id`）在一个数据日期（`data_dt`）对一只产品（`prdt_id`）在一个系统来源（`sys_source`）下以某币种（`ccy`）计的持仓。
- 每行代表什么：某客户某日某产品的一笔持仓记录（持仓数量与市值）。
- 可能的主键或唯一键：`(data_dt, pty_id, prdt_id, sys_source, ccy)`。抽样验证该组合无重复（单日/客户/产品/来源/币种唯一）。
- 日期字段和时间范围：`data_dt`（字符型 8 位，YYYYMMDD），范围 20260101–20260331，共 90 个日期。
- 适合回答的业务问题：客户持仓品种与市值、持仓市值分布、按产品/类型统计持有客户数、客户持仓集中度、持仓市值排行等。
- 使用时需要注意的限制：无空值（hold_cnt、mkt_val 均有值）；`ccy` 为字符型码（0/1/2），含义待确认（推测币种，0 可能为人民币）；`sys_source` 取值 nm/fc（nm≈普通账户、fc≈融资融券 为推测）；`hold_cnt` 为数量（numeric），`mkt_val` 为市值（numeric，单位推测为元）。

## 字段

| 字段名 | 数据类型 | 字段说明 | 示例或码值 | 来源 |
|---|---|---|---|---|
| data_dt | character varying(8) | 数据日期，YYYYMMDD | 20260130 | 用户提供 |
| pty_id | character varying(32) | 客户号（关联 ads_cust_info_d.pty_id，抽样验证 0 缺失） | C000000000000002 | 数据推测 |
| prdt_id | character varying(12) | 产品号（关联 dim_product.prdt_id，抽样验证 0 缺失） | 9900046811 | 数据推测 |
| sys_source | character varying(20) | 系统来源码：nm、fc | nm | 数据推测 |
| ccy | character varying(12) | 币种码：0、1、2 | 0 | 数据推测 |
| hold_cnt | numeric(20,4) | 持仓数量 | 16000.0000 | 数据推测 |
| mkt_val | numeric(20,4) | 持仓市值 | 4160.0000 | 数据推测 |

## 数据特征

- 抽样中发现的主要取值特征：单客户可持有多只产品（如 C000000000000002 持有多只）；多数 `ccy`=0（404785/408150），`ccy`=1 极少（270），`ccy`=2 有 3095；`sys_source` nm 361600 行、fc 46550 行；`hold_cnt`/`mkt_val` 均为 4 位小数数值。
- 空值情况：抽样与 DDL 显示关键字段 NOT NULL；hold_cnt/mkt_val 无空值（全表 0 空）。
- 码值字段：`sys_source`（nm/fc）、`ccy`（0/1/2）。
- 金额和数量字段：`hold_cnt`（数量）、`mkt_val`（市值，单位推测为元）。
- 日期字段：`data_dt`（90 个交易日历日，20260101–20260331）。
- 客户、产品、机构等标识字段：`pty_id`、`prdt_id`；无 org_id（机构归属需经 ads_cust_info_d）。
- 可能影响聚合或关联的粒度问题：单日单客户可有多行（每产品一行），按客户聚合市值需先按 `pty_id` SUM；若与按客户属性表（ads_cust_info_d）关联，是一客户对多产品持仓（一对多放大），需先聚合或按场景处理。

## 待确认

- `ccy` 各码值（0/1/2）对应币种含义。
- `sys_source`（nm/fc）业务含义（推测普通/融资融券，未人工确认）。
- `hold_cnt` 是否按手/股/份计，`mkt_val` 是否为人民币元，需人工确认。
- 主键 `(data_dt, pty_id, prdt_id, sys_source, ccy)` 是否为实际表约束需人工确认（当前为抽样唯一验证）。
