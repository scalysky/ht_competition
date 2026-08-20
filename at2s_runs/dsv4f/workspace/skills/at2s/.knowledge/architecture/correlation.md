# correlation — 表间关系

## Join 矩阵

行列均为 8 张目标表。上三角填写推测可 join 的字段（逗号分隔），对角线 `—`，下三角 `↖`。尚未确认的关系不能伪装成确定关系。

| | ads_cust_info_d | dim_branch | dim_product | dim_public | dwd_cust_hold_d | dwd_cust_tran_d | dws_cust_aset_d | dws_cust_fin_d |
|---|---|---|---|---|---|---|---|---|
| ads_cust_info_d | — | org_id | | | pty_id | pty_id | pty_id | pty_id |
| dim_branch | ↖ | — | | | | | | |
| dim_product | ↖ | ↖ | — | | prdt_id | prdt_id | | |
| dim_public | ↖ | ↖ | ↖ | — | | | | |
| dwd_cust_hold_d | ↖ | ↖ | ↖ | ↖ | — | pty_id, prdt_id, data_dt | pty_id, data_dt | pty_id, data_dt, sys_source |
| dwd_cust_tran_d | ↖ | ↖ | ↖ | ↖ | ↖ | — | pty_id, data_dt | pty_id, data_dt, sys_source |
| dws_cust_aset_d | ↖ | ↖ | ↖ | ↖ | ↖ | ↖ | — | pty_id, data_dt |
| dws_cust_fin_d | ↖ | ↖ | ↖ | ↖ | ↖ | ↖ | ↖ | — |

## 关系明细

| 表A | 表B | 关联字段 | 推断依据 | 状态 |
|---|---|---|---|---|
| ads_cust_info_d | dim_branch | org_id | 字段名相同；抽样验证 ads 的 org_id 在 dim_branch 全部存在（0 缺失）；样例 XX00000054 一致 | 推测 |
| ads_cust_info_d | dim_public | cust_lvl_cd/cust_status/gender_cd/edu_cd/prof_cd → code | 字段码值前缀与 dim_public.code_type_id 对应（100/200/500/600/700），describe 含义吻合（如 5000002=男） | 推测 |
| ads_cust_info_d | dwd_cust_hold_d | pty_id | 字段名相同；抽样验证 hold 的 pty_id 在 ads 全部存在（0 缺失）；值形态一致（C000000000000xxx） | 推测 |
| ads_cust_info_d | dwd_cust_tran_d | pty_id | 字段名相同；抽样验证 tran 的 pty_id 在 ads 全部存在（0 缺失） | 推测 |
| ads_cust_info_d | dws_cust_aset_d | pty_id | 字段名相同；抽样验证 aset 的 pty_id 在 ads 全部存在（0 缺失） | 推测 |
| ads_cust_info_d | dws_cust_fin_d | pty_id | 字段名相同；抽样验证 fin 的 pty_id 在 ads 全部存在（0 缺失） | 推测 |
| dim_product | dwd_cust_hold_d | prdt_id | 字段名相同；抽样验证 hold 的 prdt_id 在 dim_product 全部存在（0 缺失）；值形态一致（9900xxx） | 推测 |
| dim_product | dwd_cust_tran_d | prdt_id | 字段名相同；抽样验证 tran 的 prdt_id 在 dim_product 全部存在（0 缺失） | 推测 |
| dwd_cust_hold_d | dwd_cust_tran_d | pty_id, prdt_id, data_dt | 字段名相同、粒度同为客户×产品×日；样例值可对上 | 推测 |
| dwd_cust_hold_d | dws_cust_aset_d | pty_id, data_dt | 字段名相同；抽样验证 hold 的 (pty_id, data_dt) 在 aset 全部存在（0 缺失） | 推测 |
| dwd_cust_hold_d | dws_cust_fin_d | pty_id, data_dt, sys_source | 字段名相同；两者都有 sys_source（nm/fc） | 推测 |
| dwd_cust_tran_d | dws_cust_aset_d | pty_id, data_dt | 字段名相同 | 推测 |
| dwd_cust_tran_d | dws_cust_fin_d | pty_id, data_dt, sys_source | 字段名相同；两者都有 sys_source | 推测 |
| dws_cust_aset_d | dws_cust_fin_d | pty_id, data_dt | 字段名相同；抽样验证 fin 同日 (pty_id, data_dt) 绝大多数在 aset 存在（仅 4 个客户缺失） | 推测 |

未列出的表对（如 dim_branch × dim_product、dim_public × 持仓/交易等）：当前未发现直接的码值/键关联，保持空白不填。

## SQL 使用注意事项

| 注意事项 | 涉及的表 |
|---|---|
| 客户统一标识为 `pty_id`（`C`+15位数字）；`ads_cust_info_d.sor_pty_id` 为源客户号且满足 `pty_id = 'C' \|\| substr(sor_pty_id,5)`（抽样 500/500 验证），但业务含义未确认，一般不用于关联 | ads_cust_info_d、全部事实表 |
| 各事实表 `pty_id` 全部能在 `ads_cust_info_d` 找到（抽样验证 0 缺失），按 `pty_id` 关联安全；但 ads 仅 500 个客户、快照日期为 20260531，而事实表日期区间为 20260101–20260331，**ads 与事实表不要用 `data_dt` 关联**（无交集） | ads_cust_info_d、dwd/dws 事实表 |
| `ads_cust_info_d.org_id` → `dim_branch.org_id` 可补全营业部名称；`dim_branch` 存在多级层级（营业部→分公司→XX000001 财富管理部），按分公司聚合需处理 up_org 层级 | ads_cust_info_d、dim_branch |
| 产品统一标识为 `prdt_id`；持仓/交易表 `prdt_id` 全部能在 `dim_product` 找到（抽样验证 0 缺失），按 `prdt_id` 关联安全；`dim_product` 无 `data_dt`，不要与事实表按日期关联 | dim_product、dwd_cust_hold_d、dwd_cust_tran_d |
| 码值补全用 `dim_public`：`code` 关联各表码值字段，`code_type_id` 指示码域；`ads_cust_info_d` 的 cust_lvl_cd(100)/cust_status(200)/gender_cd(500)/edu_cd(600)/prof_cd(700) 对应 `dim_public.code_type_id`；关联是一对一补全，不放大行数 | dim_public、ads_cust_info_d |
| `sys_source`（nm/fc，推测普通/融资融券）在 hold/tran/fin 表中都存在；同一客户同一日可能有多行（如 fin 表 38 个客户同日 nm+fc 两行），按客户×日期聚合前需决定是否先按 sys_source 汇总或分维度 | dwd_cust_hold_d、dwd_cust_tran_d、dws_cust_fin_d |
| `ccy`（币种码 0/1/2）在 hold/tran 表中存在；hold 中 ccy 0/1/2 均有，tran 中仅 0；若需精确币种维度需保留 ccy，一般场景（人民币）可忽略 | dwd_cust_hold_d、dwd_cust_tran_d |
| 持仓表 `dwd_cust_hold_d` 唯一组合为 (data_dt, pty_id, prdt_id, sys_source, ccy)（抽样验证唯一），按客户聚合市值需先按 `pty_id` SUM，再与客户属性关联，避免一对多放大重复计数 | dwd_cust_hold_d、ads_cust_info_d |
| 交易表 `dwd_cust_tran_d` 同一 (data_dt, pty_id, prdt_id, sys_source, ccy) 可有多行（约 1.55% 重复，595 组），**不能**将 5 键组合当作唯一键；聚合买卖金额/笔数时直接对全部行 SUM | dwd_cust_tran_d |
| `dws_cust_aset_d` 为单日单客户一行（(data_dt, pty_id) 唯一），与持仓/交易关联时是一对多放大，应先聚合对方或先取资产侧 | dws_cust_aset_d、dwd_cust_hold_d、dwd_cust_tran_d |
| `dws_cust_fin_d` 单日单客户可有两行（nm/fc），与 aset（单日单客户一行）关联会放大，应先按 (pty_id, data_dt) 聚合 fin 再关联 | dws_cust_fin_d、dws_cust_aset_d |
| 日期均为字符型 YYYYMMDD（如 20260130）；持仓/资产表有 20260101–20260331 共 90 天，交易/资金表仅 20260105–20260331 共 56 个交易日，跨表联查时日期覆盖不一致 | 全部事实表 |
| `data_dt` 是字符型而非 date 类型，直接比较字符串即可，但做日期加减/区间计算需先 `::date` 转换 | 全部含 data_dt 的表 |
| 客户属性（ads）快照日为 20260531，晚于事实表末日 20260331；把 ads 当最新客户档案使用即可，日期维度以事实表为准 | ads_cust_info_d、事实表 |
| 客户姓名已脱敏（含 `*`），只能统计人数不能用于识别或文本匹配 | ads_cust_info_d |
| 金额字段均为 numeric(20,4)，`nm_tot_aset`/`nm_bal`/`mkt_val`/买卖金额等口径（总资产/资金余额/市值/交易金额）与单位（推测元）未人工确认，汇总前按问题语义选取字段 | dwd_cust_hold_d、dwd_cust_tran_d、dws_cust_aset_d、dws_cust_fin_d |
