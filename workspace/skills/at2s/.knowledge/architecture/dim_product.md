# dim_product — 产品属性维表

## 表描述

产品属性维表，334694 行，含产品ID、名称与两级分类（一级 `up_prdt_type_*` / 二级 `prdt_type_*`）。（来源：数据推测）

一级分类（12 类）：权证、债券、股票、开放式基金、衍生品、理财产品、回购一级类别、OTC产品、恒生多金融产品、证券投资类私募、贵金属、现金类。（来源：数据推测）

**分类层级不自洽（重要）**：`prdt_type_id → up_prdt_type_id` 不是函数依赖——同一二级分类ID可挂多个一级分类（如 `PT090100 OTC产品` 同时出现在 `PT080000 回购` 与 `PT090000 恒生多金融产品` 下；`PT040300` 同时是 `沪港通` 和 `H股`；`PT040600` 同时是 `传统三板` 和 `代办股份转让`）。**按一级分类筛选时直接用行上的 `up_prdt_type_id`/`up_prdt_type_name` 字段，不要先定二级再推导一级**。（来源：数据推测）

## 字段

| 字段 | 类型 | 说明 | 来源 |
|---|---|---|---|
| prdt_id | varchar(12) | 产品ID，数字串如 `9900046811`，关联 `dwd_cust_hold_d` / `dwd_cust_tran_d` | 用户提供 |
| prdt_name | varchar(100) | 产品名称 | 用户提供 |
| sor_prdt_id | varchar(12) | 产品代码 | 用户提供 |
| market_id | varchar(50) | 市场（DDL 无注释，语义待确认） | 数据推测 |
| prdt_type_id | varchar(12) | 产品二级分类ID，`PTxxxxxx` | 用户提供 |
| prdt_type_name | varchar(40) | 产品二级分类名称 | 用户提供 |
| up_prdt_type_id | varchar(12) | 产品一级分类ID，`PTxxxxxx` | 用户提供 |
| up_prdt_type_name | varchar(40) | 产品一级分类名称 | 用户提供 |
