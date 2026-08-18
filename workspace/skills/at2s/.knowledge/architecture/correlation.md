# correlation — 表间关系

## 一、join 矩阵

表顺序：ads_cust_info_d / dws_cust_aset_d / dws_cust_fin_d / dwd_cust_hold_d / dwd_cust_tran_d / dim_product / dim_branch / dim_public

| | ads_cust_info_d | dws_cust_aset_d | dws_cust_fin_d | dwd_cust_hold_d | dwd_cust_tran_d | dim_product | dim_branch | dim_public |
|---|---|---|---|---|---|---|---|---|
| ads_cust_info_d | — | pty_id, data_dt | pty_id, data_dt | pty_id, data_dt | pty_id, data_dt | | org_id | cust_lvl_cd, cust_status, gender_cd, edu_cd, prof_cd |
| dws_cust_aset_d | ↖ | — | pty_id, data_dt | pty_id, data_dt | pty_id, data_dt | | | |
| dws_cust_fin_d | ↖ | ↖ | — | pty_id, data_dt, sys_source | pty_id, data_dt, sys_source | | | |
| dwd_cust_hold_d | ↖ | ↖ | ↖ | — | pty_id, data_dt, prdt_id, sys_source, ccy | prdt_id | | |
| dwd_cust_tran_d | ↖ | ↖ | ↖ | ↖ | — | prdt_id | | |
| dim_product | ↖ | ↖ | ↖ | ↖ | ↖ | — | | |
| dim_branch | ↖ | ↖ | ↖ | ↖ | ↖ | ↖ | — | |
| dim_public | ↖ | ↖ | ↖ | ↖ | ↖ | ↖ | ↖ | — |

> 矩阵中空白单元格 = 关系未分析；`∅` = 确证无关系（本数据集暂未发现确证孤立的表，故无 `∅`）。

## 二、关系明细

| 表对 | join 字段 | 推断依据 | 状态 |
|---|---|---|---|
| ads_cust_info_d ↔ dws_cust_aset_d | pty_id, data_dt | 字段同名同型，pty_id 形态一致（C+15位数字） | 推测 |
| ads_cust_info_d ↔ dws_cust_fin_d | pty_id, data_dt | 同上 | 推测 |
| ads_cust_info_d ↔ dwd_cust_hold_d | pty_id, data_dt | 同上 | 推测 |
| ads_cust_info_d ↔ dwd_cust_tran_d | pty_id, data_dt | 同上 | 推测 |
| ads_cust_info_d ↔ dim_branch | org_id | ads.org_id 为 dim_branch.org_id 的子集（28/312） | 推测 |
| ads_cust_info_d ↔ dim_public | cust_lvl_cd/cust_status/gender_cd/edu_cd/prof_cd → code（须带 code_type_id 过滤） | 抽样验证：cust_lvl_cd 的 6 个值全部命中 dim_public(type 100) | 推测 |
| dws_cust_aset_d ↔ dws_cust_fin_d | pty_id, data_dt | 字段同名同型 | 推测 |
| dws_cust_aset_d ↔ dwd_cust_hold_d | pty_id, data_dt | 字段同名同型（aset 无 sys_source） | 推测 |
| dws_cust_aset_d ↔ dwd_cust_tran_d | pty_id, data_dt | 字段同名同型（aset 无 sys_source） | 推测 |
| dws_cust_fin_d ↔ dwd_cust_hold_d | pty_id, data_dt, sys_source | 共享三键 | 推测 |
| dws_cust_fin_d ↔ dwd_cust_tran_d | pty_id, data_dt, sys_source | 共享三键 | 推测 |
| dwd_cust_hold_d ↔ dwd_cust_tran_d | pty_id, data_dt, prdt_id, sys_source, ccy | 同粒度（客户+产品+日期+来源+币种） | 推测 |
| dwd_cust_hold_d ↔ dim_product | prdt_id | 字段同名同型 | 推测 |
| dwd_cust_tran_d ↔ dim_product | prdt_id | 字段同名同型 | 推测 |
| dim_branch ↔ dim_branch | up_org_id → org_id | 自关联形成营业部→分公司层级 | 推测 |

## 三、注意事项（生成 SQL 前必读）

| 注意事项 | 涉及的表 |
|---|---|
| 日期字段均为字符型 `varchar(8)` YYYYMMDD，区间/比较需字符串比较或显式 `TO_DATE` 转换，不能直接做数值运算 | 全部事实表、dim_branch、ads_cust_info_d |
| `ads_cust_info_d` 仅含 `20260531` 单日快照，而日事实表覆盖 2026Q1（01-01~03-31）；按 pty_id 关联并非同一时点，跨表统计需注意口径与时点不一致 | ads_cust_info_d 与其余事实表 |
| `dws_cust_aset_d` 无 `sys_source` 字段，与 fin/hold/tran 关联时无法按系统来源对齐，需明确是否忽略该维度 | dws_cust_aset_d |
| `sys_source`(nm/fc)、`ccy`(0/1/2)、`cust_type`('P') 为独立枚举，含义见各表字段备注，**不在 dim_public 内**；ccy 用数字 0/1/2，不要去 dim_public 找 | dws_cust_fin_d、dwd_cust_hold_d、dwd_cust_tran_d、ads_cust_info_d |
| 码值字段关联 dim_public 时必须带 `code_type_id` 过滤，否则不同码类型（100~700）可能撞码 | ads_cust_info_d、dim_public |
| `dim_branch.org_id` ↔ `ads_cust_info_d.org_id`；branch 表内 `up_org_id` 自关联形成层级（营业部→分公司），上级机构也在 org_id 中 | dim_branch、ads_cust_info_d |
| 资产/金额/市值字段单位需确认（推测为人民币元；持有/交易表另有 `ccy` 区分币种，金额应与 ccy 配套解读） | dws_cust_aset_d、dws_cust_fin_d、dwd_cust_hold_d、dwd_cust_tran_d |
| `dwd_cust_hold_d` 与 `dwd_cust_tran_d` 同粒度可全键关联；与 `dws_cust_fin_d` 仅共享 pty_id+data_dt+sys_source（无 prdt_id/ccy） | dwd_cust_hold_d、dwd_cust_tran_d、dws_cust_fin_d |
