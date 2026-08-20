# dws_cust_fin_d

## 表描述

- 表的业务含义：客户资金往来汇总事实表（DWS 层），按客户、数据日期、系统来源汇总资金流入流出（现金存取、转账、划拨等）。
- 数据粒度：一行 = 一个客户（`pty_id`）在一个数据日期（`data_dt`）在一个系统来源（`sys_source`）下的资金出入汇总。
- 每行代表什么：某客户某日某系统来源下的资金流入/流出金额（含现金存取、转账、划拨三个口径）。
- 可能的主键或唯一键：`(data_dt, pty_id, sys_source)`。抽样显示同客户同日可有 nm 与 fc 两行（38 个客户同日两种 sys_source 都有），故主键需含 sys_source。
- 日期字段和时间范围：`data_dt`（字符型 8 位，YYYYMMDD），范围 20260105–20260331，共 56 个日期（交易日）。
- 适合回答的业务问题：客户资金净流入/净流出、现金存取规模、转账（tran）规模、划拨（assign）规模、按系统来源（普通/融资融券）分析资金行为、资金异常大额变动等。
- 使用时需要注意的限制：同一客户同一日可能有两行（nm 与 fc），直接按 pty_id+data_dt 聚合会把两种来源加总，需按场景决定是否保留 sys_source 维度；`cash_in`/`cash_out`（现金存取）、`tran_in`/`tran_out`（推测转账）、`assign_in`/`assign_out`（推测划拨）口径未确认。

## 字段

| 字段名 | 数据类型 | 字段说明 | 示例或码值 | 来源 |
|---|---|---|---|---|
| data_dt | character varying(8) | 数据日期，YYYYMMDD | 20260130 | 用户提供 |
| pty_id | character varying(32) | 客户号（关联 ads_cust_info_d.pty_id，抽样验证 0 缺失） | C000000000000005 | 数据推测 |
| sys_source | character varying(20) | 系统来源码：nm、fc | nm | 数据推测 |
| cash_in | numeric(20,4) | 现金转入金额（推测，元） | 0.0000 | 数据推测 |
| cash_out | numeric(20,4) | 现金转出金额（推测，元） | 120000.0000 | 数据推测 |
| tran_in | numeric(20,4) | 转账转入金额（推测，元） | 0.0000 | 数据推测 |
| tran_out | numeric(20,4) | 转账转出金额（推测，元） | 0.0000 | 数据推测 |
| assign_in | numeric(20,4) | 划拨转入金额（推测，元） | 0.0000 | 数据推测 |
| assign_out | numeric(20,4) | 划拨转出金额（推测，元） | 0.0000 | 数据推测 |

## 数据特征

- 抽样中发现的主要取值特征：大量行各金额为 0；`cash_out` 可出现大额（如 120000、1000000）；`sys_source` nm 3733 行、fc 1159 行；同客户同日可有 nm/fc 两行（38 个客户）。
- 空值情况：全表无空值（抽样与 DDL）。
- 码值字段：`sys_source`（nm/fc）。
- 金额和数量字段：6 个金额字段（均为 numeric(20,4)）。
- 日期字段：`data_dt`（56 个交易日，20260105–20260331）。
- 客户、产品、机构等标识字段：`pty_id`；无 prdt_id、无 org_id。
- 可能影响聚合或关联的粒度问题：同客户同日可有两行（nm/fc），聚合时若忽略 sys_source 会重复计数；与 dws_cust_aset_d 关联时 aset 单日单客户一行而 fin 可能两行（关联会放大，需先聚合 fin 到 pty+data_dt）。

## 待确认

- `cash_in`/`cash_out`/`tran_in`/`tran_out`/`assign_in`/`assign_out` 的精确业务口径（现金存取/转账/划拨为推测）。
- `sys_source` nm/fc 的确切含义（推测普通/融资融券）。
- 金额单位（推测元）。
- 主键 `(data_dt, pty_id, sys_source)` 是否为实际约束需人工确认。
- 日期仅 56 个交易日（20260105 起）而 aset/hold 为 90 天（20260101 起），时间覆盖不一致。
