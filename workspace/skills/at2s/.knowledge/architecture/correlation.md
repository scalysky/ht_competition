# correlation.md — 表间关系

关系依据：字段名与注释语义（来自 `表描述.sql`）+ 抽样值域重叠实测。
`表描述.sql` 未声明任何外键约束，故所有关系均为**推测**，但下列每条都有 100% 或接近 100% 的值域重叠支撑。

## 一、join 矩阵

只填上三角，下三角一律 `↖`（矩阵对称），对角线 `—`。单元格取值：

- 可 join 的字段名 → 有关系
- **留空** → 尚未分析或关系未确定（会被 kb-check 归入待补充）
- **`∅`** → 已确证与该表无关系（需充分证据或用户说明），标记为孤立，不再提示补充

| | ads_cust_info_d | dim_branch | dim_product | dim_public | dwd_cust_hold_d | dwd_cust_tran_d | dws_cust_aset_d | dws_cust_fin_d |
|---|---|---|---|---|---|---|---|---|
| ads_cust_info_d | — | org_id | | 5 个码值字段 = code | pty_id | pty_id | pty_id | pty_id |
| dim_branch | ↖ | — | | | | | | |
| dim_product | ↖ | ↖ | — | | prdt_id | prdt_id | | |
| dim_public | ↖ | ↖ | ↖ | — | | | | |
| dwd_cust_hold_d | ↖ | ↖ | ↖ | ↖ | — | pty_id, prdt_id, data_dt, sys_source, ccy | pty_id, data_dt | pty_id, data_dt, sys_source |
| dwd_cust_tran_d | ↖ | ↖ | ↖ | ↖ | ↖ | — | pty_id, data_dt | pty_id, data_dt, sys_source |
| dws_cust_aset_d | ↖ | ↖ | ↖ | ↖ | ↖ | ↖ | — | pty_id, data_dt |
| dws_cust_fin_d | ↖ | ↖ | ↖ | ↖ | ↖ | ↖ | ↖ | — |

**孤岛表：无。** 8 张表每张都至少有一个非空非对角单元格。

`dim_branch` 与 `dim_public` 各自只与 `ads_cust_info_d` 相连——两张维表都靠客户主档中转，
与事实表无直接关联。要按营业部/分公司或客户属性切分事实数据，必须经 `ads_cust_info_d` 中转。

## 二、关系明细

| 表对 | join 字段 | 推断依据 | 状态 |
|---|---|---|---|
| ads_cust_info_d × dim_branch | `org_id` = `org_id` | 注释均为营业部 ID；28 个取值 100% 命中 | 推测 |
| ads_cust_info_d × dim_public | `cust_lvl_cd` = `code` and `code_type_id='100'` | 码值前 3 位 = `code_type_id`；6 个取值 100% 命中 | 推测 |
| ads_cust_info_d × dim_public | `cust_status` = `code` and `code_type_id='200'` | 同上；3 个取值 100% 命中 | 推测 |
| ads_cust_info_d × dim_public | `gender_cd` = `code` and `code_type_id='500'` | 同上；2 个取值 100% 命中 | 推测 |
| ads_cust_info_d × dim_public | `edu_cd` = `code` and `code_type_id='600'` | 同上；7 个取值 100% 命中 | 推测 |
| ads_cust_info_d × dim_public | `prof_cd` = `code` and `code_type_id='700'` | 同上；31 个取值 100% 命中 | 推测 |
| ads_cust_info_d × dwd_cust_hold_d | `pty_id` | 注释同为客户号；463 个取值 100% 命中 | 推测 |
| ads_cust_info_d × dwd_cust_tran_d | `pty_id` | 同上；385 个取值 100% 命中 | 推测 |
| ads_cust_info_d × dws_cust_aset_d | `pty_id` | 同上；487 个取值 100% 命中 | 推测 |
| ads_cust_info_d × dws_cust_fin_d | `pty_id` | 同上；380 个取值 100% 命中 | 推测 |
| dim_product × dwd_cust_hold_d | `prdt_id` | 注释同为产品 ID；3755 个取值 100% 命中 | 推测 |
| dim_product × dwd_cust_tran_d | `prdt_id` | 同上；3127 个取值 100% 命中 | 推测 |
| dwd_cust_hold_d × dwd_cust_tran_d | `pty_id`, `prdt_id`, `data_dt`, `sys_source`, `ccy` | 五字段同名同义；但日期集合不同（90 vs 56） | 推测 |
| dwd_cust_hold_d × dws_cust_aset_d | `pty_id`, `data_dt` | 同名同义；日期集合均 90 天且一致 | 推测 |
| dwd_cust_hold_d × dws_cust_fin_d | `pty_id`, `data_dt`, `sys_source` | 同名同义；日期集合不同（90 vs 56） | 推测 |
| dwd_cust_tran_d × dws_cust_aset_d | `pty_id`, `data_dt` | 同名同义；日期集合不同（56 vs 90） | 推测 |
| dwd_cust_tran_d × dws_cust_fin_d | `pty_id`, `data_dt`, `sys_source` | 同名同义；日期集合均 56 天且一致 | 推测 |
| dws_cust_aset_d × dws_cust_fin_d | `pty_id`, `data_dt` | 同名同义；日期集合不同（90 vs 56） | 推测 |
| dim_branch 自引用 | `up_org_id` → `org_id` | 上级机构自身也是本表一行；26/27 命中（96.3%） | 推测 |

## 三、注意事项

生成 SQL 前通读全部条目。

| # | 注意事项 | 涉及的表 |
|---|---|---|
| 1 | `data_dt` 存储类型是 `varchar(8)`，一律用 `'YYYYMMDD'` 字符串比较，禁止与 date/int 混用；区间用闭区间显式写全 | ads_cust_info_d、dim_branch、dwd_cust_hold_d、dwd_cust_tran_d、dws_cust_aset_d、dws_cust_fin_d |
| 2 | 关联码值字典时**必须同时限定 `code_type_id`**；一个查询关联多类码值时用不同别名，各自带自己的 `code_type_id` | ads_cust_info_d、dim_public |
| 3 | 中文筛选值要写字典里的准确全名（如客户等级为`紫金理财钻石卡客户`而非口语`钻石卡`），不要把口语简称直接塞进 SQL | dim_public、dim_product |
| 4 | `ads_cust_info_d` 与 `dim_branch` 的 `data_dt` 是 `20260531`，**落在所有事实表区间（1–3 月）之外**。关联时只用 `pty_id` / `org_id`，**关联条件不能带 `data_dt`**，否则结果为空 | ads_cust_info_d、dim_branch + 全部事实表 |
| 5 | 交易/资金表仅 56 个日期（疑为交易日），持仓/资产表有 90 个（自然日）。按 `data_dt` 内连接会静默丢约 34 天，算日均类指标时分母易错 | dwd_cust_tran_d、dws_cust_fin_d、dwd_cust_hold_d、dws_cust_aset_d |
| 6 | `dws_cust_aset_d` **没有 `sys_source` 字段**（普通/信用靠 `nm_*`/`fc_*` 列名区分），与含 `sys_source` 的表关联时不能把它当 join 键 | dws_cust_aset_d、dwd_cust_hold_d、dwd_cust_tran_d、dws_cust_fin_d |
| 7 | `dwd_cust_hold_d` 的 `ccy` 存在 `0`/`1`/`2` 三种币种，`sum(mkt_val)` 会跨币种相加；汇总市值时要么限定 `ccy='0'`，要么按币种分组。`dwd_cust_tran_d` 仅 `0`，无此问题 | dwd_cust_hold_d |
| 8 | 金额、份额字段参与聚合或相加前一律 `coalesce(x, 0)`，事实表存在空值 | 全部事实表 |
| 9 | 按产品名筛选时，`dim_product.prdt_name` **存在重名**，可能命中多个 `prdt_id`；必要时同时限定 `prdt_type_name` 或 `market_id` | dim_product、dwd_cust_hold_d、dwd_cust_tran_d |
| 10 | 客户只挂在营业部一级，按分公司口径汇总必须经 `dim_branch` 把 `org_id` 抬到 `up_org_name` | ads_cust_info_d、dim_branch |
| 11 | `dim_branch`、`dim_public` 与事实表无直接关系，必须经 `ads_cust_info_d` 中转 | dim_branch、dim_public + 全部事实表 |
| 12 | `dwd_cust_hold_d` 是**快照表**：问“某时点持有”取单个 `data_dt`，问“区间内持有过”需在区间内 distinct，二者结果不同不可混用 | dwd_cust_hold_d |

## 四、各表 `data_dt` 覆盖速查

| 表 | `data_dt` 覆盖 |
|---|---|
| ads_cust_info_d | 仅 `20260531` 单值 |
| dim_branch | 仅 `20260531` 单值 |
| dim_product / dim_public | 无此字段 |
| dwd_cust_hold_d / dws_cust_aset_d | `20260101`–`20260331`，90 天（自然日） |
| dwd_cust_tran_d / dws_cust_fin_d | `20260105`–`20260331`，56 天（疑为交易日） |
