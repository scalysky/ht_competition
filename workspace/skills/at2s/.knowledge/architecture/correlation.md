# correlation — 表间关系

## 一、join 矩阵

|  | ads_cust_info_d | dim_branch | dim_product | dim_public | dwd_cust_hold_d | dwd_cust_tran_d | dws_cust_aset_d | dws_cust_fin_d |
|---|---|---|---|---|---|---|---|---|
| ads_cust_info_d | — | org_id | ∅ | cust_lvl_cd, cust_status, gender_cd, edu_cd, prof_cd (=code) | pty_id | pty_id | pty_id | pty_id |
| dim_branch | ↖ | — | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ |
| dim_product | ↖ | ↖ | — | ∅ | prdt_id | prdt_id | ∅ | ∅ |
| dim_public | ↖ | ↖ | ↖ | — | ∅ | ∅ | ∅ | ∅ |
| dwd_cust_hold_d | ↖ | ↖ | ↖ | ↖ | — | pty_id, prdt_id | pty_id | pty_id |
| dwd_cust_tran_d | ↖ | ↖ | ↖ | ↖ | ↖ | — | pty_id | pty_id |
| dws_cust_aset_d | ↖ | ↖ | ↖ | ↖ | ↖ | ↖ | — | pty_id |
| dws_cust_fin_d | ↖ | ↖ | ↖ | ↖ | ↖ | ↖ | ↖ | — |

- 上三角为可 join 字段；`↖` 见上三角；`—` 对角线；`∅` 已确证无直接 join。
- `dim_branch` 除 `ads_cust_info_d` 外全为 `∅`，但**非孤立**：经 `ads_cust_info_d`（pty_id↔org_id 两跳）可达各事实表，见关系明细。

## 二、关系明细

| 表对 | join 字段 | 推断依据 | 状态 |
|---|---|---|---|
| ads_cust_info_d × dim_branch | ads.org_id = branch.org_id | 同名字段 org_id；抽样 500/500 命中；格式一致 `XX`+8 位 | 推测 |
| ads_cust_info_d × dim_public | ads.{cust_lvl_cd, cust_status, gender_cd, edu_cd, prof_cd} = public.code（配 code_type_id=100/200/500/600/700） | 5 个码值字段全部命中字典（0 缺失）；code 前 3 位=code_type_id | 推测 |
| ads_cust_info_d × dwd_cust_hold_d | pty_id | 同名 pty_id；格式一致 `C`+15 位；hold 客户 463 人全在 ads | 推测 |
| ads_cust_info_d × dwd_cust_tran_d | pty_id | 同上；tran 客户 385 人全在 ads | 推测 |
| ads_cust_info_d × dws_cust_aset_d | pty_id | 同上；aset 全部 pty_id 均可在 ads 找到 | 推测 |
| ads_cust_info_d × dws_cust_fin_d | pty_id | 同上；fin 客户 380 人全在 ads | 推测 |
| dim_product × dwd_cust_hold_d | prdt_id | 同名 prdt_id；hold 的 3,755 个产品全部命中 dim_product | 推测 |
| dim_product × dwd_cust_tran_d | prdt_id | 同上；tran 的 3,127 个产品全部命中 dim_product | 推测 |
| dwd_cust_hold_d × dwd_cust_tran_d | pty_id, prdt_id | 同名复合键；同为"客户×产品"粒度事实表 | 推测 |
| dwd_cust_hold_d × dws_cust_aset_d | pty_id | 同名 pty_id；同为客户级 | 推测 |
| dwd_cust_hold_d × dws_cust_fin_d | pty_id | 同上 | 推测 |
| dwd_cust_tran_d × dws_cust_aset_d | pty_id | 同上 | 推测 |
| dwd_cust_tran_d × dws_cust_fin_d | pty_id | 同上 | 推测 |
| dws_cust_aset_d × dws_cust_fin_d | pty_id | 同上 | 推测 |
| dim_branch ×（其余 6 表） | 无直接 join | 事实表无 org_id；branch 需经 ads_cust_info_d 两跳接入 | 推测 |
| dim_public ×（dwd/dws 4 张事实表） | 无直接 join | 事实表的 sys_source(nm/fc)、ccy(0/1/2) 不在字典 | 推测 |
| dim_product × dim_public | 无 | prdt_type_id 为 `PTxxx`，不在字典 | 推测 |
| dim_branch × dim_public | 无 | branch 无码值字段 | 推测 |
| ads_cust_info_d × dim_product | 无 | 无公共字段 | 推测 |

## 三、注意事项

| 注意事项 | 涉及的表 |
|---|---|
| **日期口径错位**：ads_cust_info_d 与 dim_branch 只有 20260531 单日快照，而 dwd/dws 事实表是 20260101–20260331。关联时**只按 pty_id（或 org_id）join，不要加 data_dt 相等条件**，否则会因日期无交集而丢光所有行。 | ads_cust_info_d、dim_branch、dwd_cust_hold_d、dwd_cust_tran_d、dws_cust_aset_d、dws_cust_fin_d |
| **码值翻译走 dim_public**：cust_lvl_cd / cust_status / gender_cd / edu_cd / prof_cd 是 7 位码值，须 join dim_public.code（配 code_type_id）才能得到中文含义；`cust_type`('P')、`sys_source`(nm/fc)、`ccy`(0/1/2) **不在字典**，直接按字面值用。 | ads_cust_info_d、dim_public、dwd_cust_hold_d、dwd_cust_tran_d、dws_cust_fin_d |
| **dwd_cust_tran_d 一键多行**：(data_dt,pty_id,prdt_id,sys_source,ccy) 有 595 组重复，聚合必须 SUM，不能假定唯一；买卖次数用 SUM(buy_cnt)/SUM(sell_cnt)。 | dwd_cust_tran_d |
| **数量≠金额**：buy_mnt/sell_mnt/hold_cnt 是份额/股数，buy_amt/sell_amt/mkt_val 才是金额，统计金额勿误用数量字段。 | dwd_cust_hold_d、dwd_cust_tran_d |
| **分支两跳**：要按营业部/分公司统计持仓或交易，路径为 事实表(pty_id)→ads_cust_info_d(org_id)→dim_branch，不能直连。 | dim_branch、ads_cust_info_d、dwd_cust_hold_d、dwd_cust_tran_d、dws_cust_aset_d、dws_cust_fin_d |
| **产品分类名称有歧义**：dim_product 的 prdt_type_id/up_prdt_type_id 与名称非严格一对一（如 PT040300 既是沪港通又是 H 股），按分类过滤优先用 ID，用名称需人工核对。 | dim_product |
| **外币市值口径未定**：dwd_cust_hold_d 的 mkt_val 对 ccy=1/2（美元/港币）是否已折算人民币未确认，跨币种汇总前先与用户确认。 | dwd_cust_hold_d |
