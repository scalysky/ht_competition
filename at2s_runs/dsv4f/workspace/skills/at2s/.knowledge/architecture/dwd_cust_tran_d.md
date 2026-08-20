# dwd_cust_tran_d

## 表描述

- 表的业务含义：客户交易明细事实表（DWD 层），记录每个客户在每个数据日期对每只产品的买入/卖出交易汇总（数量、金额、手续费等，按系统来源、币种展开）。
- 数据粒度：一行 = 一个客户（`pty_id`）在一个数据日期（`data_dt`）对一只产品（`prdt_id`）在一个系统来源（`sys_source`）下以某币种（`ccy`）计的当日买入/卖出交易汇总。注意：抽样发现同一 (data_dt, pty_id, prdt_id, sys_source, ccy) 组合可出现多行（595 组重复），实际粒度可能更细（如按交易批次/账户），不可将该组合视为唯一键。
- 每行代表什么：某客户某日某产品的一笔（或一批）买入/卖出交易汇总。
- 可能的主键或唯一键：无明确唯一键；`(data_dt, pty_id, prdt_id, sys_source, ccy)` 存在重复（39060 行对 38461 个唯一组合，重复率约 1.55%）。
- 日期字段和时间范围：`data_dt`（字符型 8 位，YYYYMMDD），范围 20260105–20260331，共 56 个日期（均为交易日）。
- 适合回答的业务问题：客户交易活跃度（买卖次数）、交易金额、佣金/手续费、按产品统计交易量、按客户/产品/类型聚合交易等。
- 使用时需要注意的限制：聚合时应对全表行进行 SUM（同一客户/产品/日期存在多行代表多笔交易，直接 GROUP BY 上述 5 键会合并多笔交易，若需精确需谨慎）；`ccy` 抽样全部为 0；`sys_source` nm/fc；各金额/数量字段均为 4 位小数；`buy_rake`/`sell_rake` 推测为佣金，`buy_fare`/`sell_fare` 推测为手续费/费用（未确认）。

## 字段

| 字段名 | 数据类型 | 字段说明 | 示例或码值 | 来源 |
|---|---|---|---|---|
| data_dt | character varying(8) | 数据日期，YYYYMMDD | 20260130 | 用户提供 |
| pty_id | character varying(32) | 客户号（关联 ads_cust_info_d.pty_id，抽样验证 0 缺失） | C000000000000002 | 数据推测 |
| prdt_id | character varying(12) | 产品号（关联 dim_product.prdt_id，抽样验证 0 缺失） | 9900263487 | 数据推测 |
| sys_source | character varying(20) | 系统来源码：nm、fc | nm | 数据推测 |
| ccy | character varying(12) | 币种码：0（抽样仅此值） | 0 | 数据推测 |
| buy_cnt | integer | 买入笔数/次数 | 1 | 数据推测 |
| buy_mnt | numeric(20,4) | 买入数量 | 2500.0000 | 数据推测 |
| buy_rake | numeric(20,4) | 买入佣金 | 3.0400 | 数据推测 |
| buy_amt | numeric(20,4) | 买入金额 | 8675.0000 | 数据推测 |
| buy_fare | numeric(20,4) | 买入手续费/费用 | 0.0900 | 数据推测 |
| sell_cnt | integer | 卖出笔数/次数 | 2 | 数据推测 |
| sell_mnt | numeric(20,4) | 卖出数量 | 2500.0000 | 数据推测 |
| sell_rake | numeric(20,4) | 卖出佣金 | 3.4300 | 数据推测 |
| sell_amt | numeric(20,4) | 卖出金额 | 8725.0000 | 数据推测 |
| sell_fare | numeric(20,4) | 卖出手续费/费用 | 4.4400 | 数据推测 |

## 数据特征

- 抽样中发现的主要取值特征：同一客户单日可交易多只产品；`ccy` 全表仅 0；`sys_source` nm 34183 行、fc 4877 行；buy/sell 各字段在无交易时以 0 填充；数量与金额为 4 位小数，cnt 为整数。
- 空值情况：DDL 关键字段 NOT NULL；金额/数量字段无空值（抽样）。
- 码值字段：`sys_source`（nm/fc）、`ccy`（0）。
- 金额和数量字段：`buy_mnt`/`sell_mnt`（数量）、`buy_amt`/`sell_amt`（金额，推测元）、`buy_rake`/`sell_rake`（佣金）、`buy_fare`/`sell_fare`（费用）。
- 日期字段：`data_dt`（56 个交易日，20260105–20260331）。
- 客户、产品、机构等标识字段：`pty_id`、`prdt_id`；无 org_id。
- 可能影响聚合或关联的粒度问题：同一 (data_dt, pty_id, prdt_id, sys_source, ccy) 可有多行（多笔交易），若将该组合当唯一键会丢失明细；与 ads 客户属性表关联为一对多，需先聚合交易再关联客户属性；与 dwd_cust_hold_d 关联时两者都是客户×产品×日期粒度，需注意交易表同一客户产品可能有 N 行而持仓表只有 1 行。

## 待确认

- 表内实际唯一键/隐含批次字段（为何同一客户产品日期出现多行）需人工确认。
- `buy_rake`/`sell_rake`、`buy_fare`/`sell_fare` 的确切含义（佣金/手续费口径）。
- `ccy` 码值与币种对应关系（抽样仅 0）。
- `sys_source`（nm/fc）业务含义（推测普通/融资融券）。
- 金额单位（推测元）及数量单位需人工确认。
