# correlation.md — 表间关系

## 一、join 矩阵

| | ads_cust_info_d | dim_branch | dim_product | dim_public | dwd_cust_hold_d | dwd_cust_tran_d | dws_cust_aset_d | dws_cust_fin_d |
|---|---|---|---|---|---|---|---|---|
| ads_cust_info_d | — | org_id | ∅ | code+code_type_id | pty_id | pty_id | pty_id | pty_id |
| dim_branch | ↖ | — | ∅ | ∅ | ∅ | ∅ | ∅ | ∅ |
| dim_product | ↖ | ↖ | — | ∅ | prdt_id | prdt_id | ∅ | ∅ |
| dim_public | ↖ | ↖ | ↖ | — | ∅ | ∅ | ∅ | ∅ |
| dwd_cust_hold_d | ↖ | ↖ | ↖ | ↖ | — | pty_id, data_dt, prdt_id, sys_source, ccy | pty_id, data_dt | pty_id, data_dt, sys_source |
| dwd_cust_tran_d | ↖ | ↖ | ↖ | ↖ | ↖ | — | pty_id, data_dt | pty_id, data_dt, sys_source |
| dws_cust_aset_d | ↖ | ↖ | ↖ | ↖ | ↖ | ↖ | — | pty_id, data_dt |
| dws_cust_fin_d | ↖ | ↖ | ↖ | ↖ | ↖ | ↖ | ↖ | — |

说明：`∅` = 已确证无直接 join 键（其中 dim_branch 与事实表可经 ads_cust_info_d 的 `pty_id→org_id` 桥接，属间接关系）；空格 = 未分析。

## 二、关系明细

| 表对 | join 字段 | 推断依据 | 状态 |
|---|---|---|---|
| ads_cust_info_d × dim_branch | `ads.org_id = branch.org_id` | 字段同名；取值形态一致（`XX00000049` ↔ `XX00000001`~`XX00000312` 全集覆盖） | 推测 |
| ads_cust_info_d × dim_public | `cust_lvl_cd = code AND code_type_id='100'`（同构：cust_status/200、gender_cd/500、edu_cd/600、prof_cd/700） | ads 五个码值字段全部命中 dim_public 对应类型码表；类型 300 证件、400 风险等级在本数据集无使用方 | 推测 |
| ads_cust_info_d × dwd_cust_hold_d | `pty_id` | 字段同名，取值格式 `C00000000000000x` 一致 | 推测 |
| ads_cust_info_d × dwd_cust_tran_d | `pty_id` | 同上 | 推测 |
| ads_cust_info_d × dws_cust_aset_d | `pty_id` | 同上 | 推测 |
| ads_cust_info_d × dws_cust_fin_d | `pty_id` | 同上 | 推测 |
| dim_product × dwd_cust_hold_d | `prdt_id` | 字段同名，取值均为 10 位数字串 | 推测 |
| dim_product × dwd_cust_tran_d | `prdt_id` | 同上 | 推测 |
| dwd_cust_hold_d × dwd_cust_tran_d | `pty_id, data_dt, prdt_id, sys_source, ccy` | 两表同构同粒度（tran 侧同键多行，join 后仍需聚合） | 推测 |
| dwd_cust_hold_d × dws_cust_aset_d | `pty_id, data_dt` | 同客户同日快照对齐 | 推测 |
| dwd_cust_hold_d × dws_cust_fin_d | `pty_id, data_dt, sys_source` | 同上，fin 需额外对齐账户来源 | 推测 |
| dwd_cust_tran_d × dws_cust_aset_d | `pty_id, data_dt` | 同客户同日快照对齐 | 推测 |
| dwd_cust_tran_d × dws_cust_fin_d | `pty_id, data_dt, sys_source` | 同上 | 推测 |
| dws_cust_aset_d × dws_cust_fin_d | `pty_id, data_dt` | 同客户同日快照对齐 | 推测 |
| dim_branch × dim_branch（自引用） | `up_org_id = org_id` | 层级字段指向本表 org_id | 推测 |

## 三、注意事项

| 注意事项 | 涉及的表 |
|---|---|
| `data_dt` 是 varchar(8) `YYYYMMDD`，不是日期类型；范围过滤直接用字符串比较（`'20260301'` 格式），做日期运算先 `to_date` | 全部含 data_dt 的表 |
| 时间覆盖不一致：aset/hold 覆盖 20260101–20260331（90 天），fin/tran 只覆盖 20260105–20260331（56 天），ads/dim_branch 是 20260531 单日快照。跨表按日期对齐时不得超出各自信任区间；ads 属性与事实表 join 只用 `pty_id`，**不得加日期条件** | ads_cust_info_d、dim_branch、dws_cust_fin_d、dwd_cust_tran_d |
| 统计"客户数"必须 `COUNT(DISTINCT pty_id)`：fin/tran/hold 有 nm/fc 双账户多行，tran 还有同键多行，`COUNT(*)` 会重复计数 | dwd_cust_tran_d、dwd_cust_hold_d、dws_cust_fin_d |
| dwd_cust_tran_d 同键（data_dt+pty_id+prdt_id+sys_source+ccy）存在多行（39060 行 vs 38461 键）。成交笔数 = `SUM(buy_cnt)`/`SUM(sell_cnt)`，金额 = 对应金额字段 SUM，**禁止 COUNT(*) 当笔数** | dwd_cust_tran_d |
| `ccy` 币种：'0' 人民币、'1' 美元、'2' 港币。汇总 `mkt_val` 等金额字段前必须 `WHERE ccy='0'`（或按币种分组），否则外币市值混入人民币口径 | dwd_cust_hold_d、dwd_cust_tran_d |
| dim_public join 必须双条件：`code` + `code_type_id`。常用类型：100 客户等级、200 账户状态、500 性别、600 学历、700 职业；300 证件、400 风险等级在本数据集无使用方。筛选"有效/正常"客户用 `cust_status='2000001'`（明文"正常"） | dim_public、ads_cust_info_d |
| dim_product 分类层级不自洽：同一 `prdt_type_id` 可挂多个一级分类（PT090100、PT040300、PT040600 均有多组）。按一级分类筛选直接用行上的 `up_prdt_type_id/name`，不要经二级分类推导 | dim_product |
| dim_branch 的 DDL 注释有笔误：`up_org_id`/`up_org_name` 的 COMMENT 误写在 `org_id`/`org_name` 上，语义以上级字段为准；组织名已脱敏 | dim_branch |
| 按营业部/分公司统计客户或资产：事实表无 `org_id`，须经 `ads_cust_info_d` 桥接（ads.org_id → dim_branch.org_id），且按分公司统计时用 `up_org_*` 字段 | dim_branch、ads_cust_info_d、全部事实表 |
| 资产口径：普通+信用总资产 = `nm_tot_aset + fc_pur_aset`（aset 表无 sys_source，账户维度已拆列）；fin 表的 nm/fc 是两行，日期范围与 aset 不一致，勿直接相减对账 | dws_cust_aset_d、dws_cust_fin_d |
