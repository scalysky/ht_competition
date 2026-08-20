# correlation — 表间关系汇总

以下关系仅依据字段名、数据库类型及有限 CSV/数据库样例推断，全部状态为“推测”，未经人工确认。

## 一、Join 矩阵

| | ads_cust_info_d | dim_branch | dim_product | dim_public | dwd_cust_hold_d | dwd_cust_tran_d | dws_cust_aset_d | dws_cust_fin_d |
|---|---|---|---|---|---|---|---|---|
| ads_cust_info_d | — | org_id（可选 data_dt） |  | cust_lvl_cd/cust_status/gender_cd/edu_cd/prof_cd → code，并限定 code_type_id | pty_id | pty_id | pty_id | pty_id |
| dim_branch | ↖ | — |  |  |  |  |  |  |
| dim_product | ↖ | ↖ | — |  | prdt_id | prdt_id |  |  |
| dim_public | ↖ | ↖ | ↖ | — |  |  |  |  |
| dwd_cust_hold_d | ↖ | ↖ | ↖ | ↖ | — | data_dt, pty_id, prdt_id, sys_source, ccy | data_dt, pty_id | data_dt, pty_id, sys_source |
| dwd_cust_tran_d | ↖ | ↖ | ↖ | ↖ | ↖ | — | data_dt, pty_id | data_dt, pty_id, sys_source |
| dws_cust_aset_d | ↖ | ↖ | ↖ | ↖ | ↖ | ↖ | — | data_dt, pty_id |
| dws_cust_fin_d | ↖ | ↖ | ↖ | ↖ | ↖ | ↖ | ↖ | — |

空白表示未发现可支持的直接业务关联，不代表已确认无关系。

## 二、关系明细

| 表对 | Join 字段 | 推断依据 | 状态 |
|---|---|---|---|
| ads_cust_info_d × dim_branch | `ads_cust_info_d.org_id = dim_branch.org_id`；历史快照场景可再评估 `data_dt` | 同名字段、varchar 类型及 `XX...` 样例格式一致 | 推测 |
| ads_cust_info_d × dim_public | `cust_lvl_cd=code AND code_type_id='100'` | `100...` 前缀与公共码样例匹配 | 推测 |
| ads_cust_info_d × dim_public | `cust_status=code AND code_type_id='200'` | `200...` 码值与“正常/销户/休眠已确认”样例匹配 | 推测 |
| ads_cust_info_d × dim_public | `gender_cd=code AND code_type_id='500'` | `5000002/5000003` 与“男/女”样例匹配 | 推测 |
| ads_cust_info_d × dim_public | `edu_cd=code AND code_type_id='600'` | `600...` 与学历描述样例匹配 | 推测 |
| ads_cust_info_d × dim_public | `prof_cd=code AND code_type_id='700'` | `700...` 与职业描述样例匹配 | 推测 |
| ads_cust_info_d × dwd_cust_hold_d | `pty_id` | 同名、同类型、客户标识样例格式一致 | 推测 |
| ads_cust_info_d × dwd_cust_tran_d | `pty_id` | 同名、同类型、客户标识样例格式一致 | 推测 |
| ads_cust_info_d × dws_cust_aset_d | `pty_id` | 同名、同类型、客户标识样例格式一致 | 推测 |
| ads_cust_info_d × dws_cust_fin_d | `pty_id` | 同名、同类型、客户标识样例格式一致 | 推测 |
| dim_product × dwd_cust_hold_d | `prdt_id` | 同名、同类型、产品标识样例格式一致 | 推测 |
| dim_product × dwd_cust_tran_d | `prdt_id` | 同名、同类型、产品标识样例格式一致 | 推测 |
| dwd_cust_hold_d × dwd_cust_tran_d | `data_dt, pty_id, prdt_id, sys_source, ccy` | 五个维度字段同名同类型；两表粒度形态相近 | 推测 |
| dwd_cust_hold_d × dws_cust_aset_d | `data_dt, pty_id` | 客户日字段同名同类型；持仓表须先聚合到客户日 | 推测 |
| dwd_cust_hold_d × dws_cust_fin_d | `data_dt, pty_id, sys_source` | 三字段同名同类型；持仓表须先按目标粒度聚合 | 推测 |
| dwd_cust_tran_d × dws_cust_aset_d | `data_dt, pty_id` | 客户日字段同名同类型；交易表须先聚合到客户日 | 推测 |
| dwd_cust_tran_d × dws_cust_fin_d | `data_dt, pty_id, sys_source` | 三字段同名同类型；交易表须先按目标粒度聚合 | 推测 |
| dws_cust_aset_d × dws_cust_fin_d | `data_dt, pty_id` | 客户日字段同名同类型；资金表须先跨 `sys_source` 聚合或保留一对多 | 推测 |

## 三、SQL 使用注意事项

| 注意事项 | 涉及的表 |
|---|---|
| 日期均为 `varchar(8)`，按 `YYYYMMDD` 字符串过滤；客户快照样例日期 `20260531` 与事实表样例日期不同，客户关联事实表时通常只按 `pty_id`，不得未经确认强加等日期连接。 | ads_cust_info_d、dim_branch、四张 DWD/DWS 表 |
| `dim_public` 连接必须同时限定对应 `code_type_id`；域映射目前均为推测。 | ads_cust_info_d、dim_public |
| 客户快照连接多日事实会复制客户属性；统计客户数优先 `COUNT(DISTINCT pty_id)`。 | ads_cust_info_d、四张 DWD/DWS 表 |
| 产品维无日期字段，推测按 `prdt_id` 连接；需确认是否存在历史版本或重复产品。 | dim_product、dwd_cust_hold_d、dwd_cust_tran_d |
| DWD 持仓与交易均比客户日粒度更细，连接资产或资金表前应先聚合到目标 Join 粒度，避免行数膨胀。 | dwd_cust_hold_d、dwd_cust_tran_d、dws_cust_aset_d、dws_cust_fin_d |
| `sys_source` 与 `ccy` 码义、金额折算尚未确认；跨来源或跨币种金额不得默认直接相加。 | dwd_cust_hold_d、dwd_cust_tran_d、dws_cust_aset_d、dws_cust_fin_d |
| 交易表存在买入或卖出全零的业务行，不能仅以 `COUNT(*)` 代表交易笔数或活跃客户。 | dwd_cust_tran_d |
| 机构自关联推测使用 `org_id = up_org_id` 逐级展开，但根节点和终止规则待确认。 | dim_branch |

## 四、待人工确认的关系

- `ads_cust_info_d.org_id` 到 `dim_branch.org_id` 是否需要同时匹配 `data_dt`。
- 五个客户代码字段到 `dim_public.code_type_id` 的正式映射。
- `pty_id` 是否为五张客户相关表统一主数据标识，是否存在一客多号。
- `prdt_id` 到产品维是否始终一对一及是否需附加市场条件。
- DWD 两表的完整唯一键，以及 `sys_source`、`ccy` 是否都必须参与连接。
- `dws_cust_aset_d` 与其它事实表的资产、持仓和资金口径能否核对相加。
