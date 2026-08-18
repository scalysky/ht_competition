# dim_product — 产品属性维表

## 表描述
产品维度表，每行一个产品及其分类属性。（来源：用户提供，来自 `表描述.sql` 的 COMMENT）

实测 `prdt_id` 形如 `9900263487`（10 位数字），`prdt_type_id` 形如 `PT040100`，`up_prdt_type_id` 形如 `PT040000`，`market_id` 形如 `602010`/`602020`/`622005`（数据推测：交易所/市场代码）。

## 字段
| 字段 | 类型 | 含义 | 来源 | 备注 |
|---|---|---|---|---|
| prdt_id | varchar(12) | 产品ID | 用户提供 | 与持有/交易事实表 `prdt_id` 关联 |
| prdt_name | varchar(100) | 产品名称 | 用户提供 | |
| sor_prdt_id | varchar(12) | 产品代码 | 用户提供 | |
| market_id | varchar(50) | 市场ID | 用户提供 | 推测为交易所/市场代码，不在 dim_public 体系内 |
| prdt_type_id | varchar(12) | 产品二级分类ID | 用户提供 | 如 PT040100 |
| prdt_type_name | varchar(40) | 产品二级分类名称 | 用户提供 | |
| up_prdt_type_id | varchar(12) | 产品一级分类ID | 用户提供 | 如 PT040000 |
| up_prdt_type_name | varchar(40) | 产品一级分类名称 | 用户提供 | |

## 关系
- `prdt_type_id` ↔ `up_prdt_type_id`：产品二级分类归属一级分类（关系状态：推测）。
- `prdt_id` ↔ `dwd_cust_hold_d.prdt_id`、`dwd_cust_tran_d.prdt_id`（关系状态：推测）。

## 待确认
- `market_id` / `prdt_type_id` 等代码是否需要映射到 dim_public（实测不在 dim_public 内，属产品自身分类体系）。
