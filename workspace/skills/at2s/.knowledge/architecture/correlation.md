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
| 统计"客户数"必须 `COUNT(DISTINCT pty_id)`：fin/tran/hold 有 nm/fc 双账户多行，tran 还有同键多行，`COUNT(*)` 会重复计数；**反向规则（用户确认，train_2）**：已实测唯一的键直接 `count(*)`——dim_product.prdt_id（334694 行全唯一）、dim_branch.org_id、ads 单快照每客户一行；对唯一键加 `COUNT(DISTINCT)` 迫使全排序弃并行哈希聚合，dim_product 实测慢 5.9 倍（688ms vs 117ms） | dwd_cust_tran_d、dwd_cust_hold_d、dws_cust_fin_d、dim_product、dim_branch |
| dwd_cust_tran_d 同键（data_dt+pty_id+prdt_id+sys_source+ccy）存在多行（39060 行 vs 38461 键）。成交笔数 = `SUM(buy_cnt)`/`SUM(sell_cnt)`，金额 = 对应金额字段 SUM，**禁止 COUNT(*) 当笔数** | dwd_cust_tran_d |
| `ccy` 币种：'0' 人民币、'1' 美元、'2' 港币。**滤币种与否以题面为准**（用户确认，train_3）：题面明示币种（如"港币(ccy=2)"）才 `WHERE ccy=…`；题面未提币种的市值/金额汇总**不滤 ccy**、全币种直接 SUM，持仓客户数同口径（未提币种时全币种计客户）。与 train_1 裁决"交易金额直接 SUM 不滤 ccy"同源互证 | dwd_cust_hold_d、dwd_cust_tran_d |
| dim_public join 必须双条件：`code` + `code_type_id`。常用类型：100 客户等级、200 账户状态、500 性别、600 学历、700 职业；300 证件、400 风险等级在本数据集无使用方。筛选"有效/正常"客户用 `cust_status='2000001'`（明文"正常"） | dim_public、ads_cust_info_d |
| dim_product 分类层级不自洽：同一 `prdt_type_id` 可挂多个一级分类（PT090100、PT040300、PT040600 均有多组）。按一级分类筛选直接用行上的 `up_prdt_type_id/name`，不要经二级分类推导 | dim_product |
| dim_branch 的 DDL 注释有笔误：`up_org_id`/`up_org_name` 的 COMMENT 误写在 `org_id`/`org_name` 上，语义以上级字段为准；组织名已脱敏 | dim_branch |
| 按营业部/分公司统计客户或资产：事实表无 `org_id`，须经 `ads_cust_info_d` 桥接（ads.org_id → dim_branch.org_id），且按分公司统计时用 `up_org_*` 字段。**边界（用户确认，train_3 序号 45）：数机构行（多少家/机构分布）按字面全表统计（见 dim_branch 条）；数客户（各机构客户数/年龄等）从客户侧 inner join 统计，零客户机构不输出**；按营业部聚合客户资产时输出并 **GROUP BY org_name 单列**（脱敏同名按字面合并：ads 客户 28 个 org_id 仅对应 15 个 org_name，train_4/60 答案 15 组判对、按 org_id 分组 27 组判错；零资产客户 LEFT JOIN+COALESCE(0) 计入其营业部，详见 dim_branch.md） | dim_branch、ads_cust_info_d、全部事实表 |
| 资产口径：普通+信用总资产 = `nm_tot_aset + fc_pur_aset`（aset 表无 sys_source，账户维度已拆列）；fin 表的 nm/fc 是两行，日期范围与 aset 不一致，勿直接相减对账 | dws_cust_aset_d、dws_cust_fin_d |
| tran/hold 存在 nm/fc 双记录：同一笔交易在 sys_source='nm'/'fc' 各一行、其余业务字段完全相同（tran 全库 4606 组，持仓核对证实为重复记账）。**汇总口径按原始行直接 SUM、不去重**（用户确认，与标准答案对齐；滤币种与否以题面为准——见 ccy 条）。股票/科创板交易实测全部 ccy='0' | dwd_cust_tran_d、dwd_cust_hold_d |
| 口径偏好（用户确认）：资产/持有类指标默认取**期末 20260331 单日时点**；"日均"= `SUM(nm_tot_aset+fc_pur_aset)/90`；"各月趋势"= 按月 SUM 全部快照（train_5/69）；盈亏 = 期末总资产 − 期初总资产 + 期间净流出（fin 六字段）；详细别名见 `conventions/aliases.md` | dws_cust_aset_d、dwd_cust_hold_d、dws_cust_fin_d |
| 输出格式（用户确认）：舍入优先级（用户裁决，2026-08-25，train_7/89、90 消解 39 vs 90 批间冲突）——**题面明示精度/量纲则照抄题面，未明示一律优先 round**，精度按指标类型：年龄均值 `ROUND(x,1)`、**资产均值 `ROUND(x,2)`**（train_2 序号 39）、**合计/比值/比率 `ROUND(x,2)`**（train_7/89 比值 round 2、train_7/90 月度合计 round 2；train_2/39 合计不 round 为历史例外）、占比取百分数 `ROUND(x*100.0/…,2)`（train_3 序号 54），"数量及占比"类输出**带分母列**（cust_cnt，train_6/87 缺列判错）且 **HAVING 过滤零分子组**只输出有该特征的组（train_6/87：答案 having 高价值数>0 出 5 行，含零组 15 行判错；分母=该组全体客户数、含零资产客户）；排序默认 `ORDER BY 度量 DESC`，维度升序例外（train_2 序号 29 `order by ccy`、train_3 序号 40/46、train_4 序号 57 `order by sys_source`、62 `order by 标签`、train_7/91 `order by cust_lvl_cd`）值集等价即判对，名单类 top-N 默认 **LIMIT 固定行数、并列不扩展**（用户裁决，train_5/66/72；train_4/56、train_6/79 同款实证），题面"含并列名次"字样不触发超额、除非用户显式说明；次级键 `order by 度量 desc, pty_id` 保留作并列时取法确定性（train_4/56：第10/11名并列 53 分，pty_id 小者优先）；输出列从严模仿题库答案形态（分布类=维度+count，产品类=两级分类+金额合计，**名单类二分（train_6/88 裁决）**：客户名单=仅 pty_id 一列+可选度量列、不 join 姓名——train_3 序号 42 判错教训/51 佐证、train_6/80 pty_id-only 判对再证；产品名单=join dim_product 输出 prdt_name+prdt_type_name（**二级**分类名）并按其分组，附持有客户数+市值合计——仅输出 prdt_id 判错；筛选用一级 up_prdt_type_*、展示用名称+二级，两不相扰）；客户数在 ads（每客户一行）上 `count(*)` 与 `COUNT(DISTINCT pty_id)` 等价；分布/统计类问题默认**全体客户、不加 cust_status 过滤**（除非题目明示"正常/有效"）；标准答案习惯带 ads 单快照日期条件 `data_dt='20260531'`（单快照下与不带等价，带上无害）；标准答案 SQL 自身有 bug 时保持语义正确、不复刻；地理维度双列："各城市"类输出省+市双维度列（prov_name, city_name, cnt, avg_age），数值全同但缺省份列仍判错（train_4/55）；分档段数与标签（train_6/82、83 裁决后重写）：**题面明示分档则照抄**（train_1/2 四段、train_4/62 四段、train_6/82 三档，实例全一致）；题面未明示则盲拍、**不锚定任何先例**（用户确认，train_6/83 答案三段 '<30'/'[30,50)'/'[50,)' 仅孤例不复制）；**标签量纲贴题面**——题面带"万"标签必须带"万"（train_6/82：'<100000' 判错、'<10万'/'[10万,50万)'/'50万以上' 对）；年龄段标签纯区间记号 '<30'/'[30,50)'/'[50,60)'/'[60,)'（train_1/2、train_4/62、train_6/83 三实例一致，哪怕题面纯中文也被规范化）；分档边界一律左闭右开含端点（"X以上"含 X，train_6/82 十万整归中档佐证）；末档"X以上"两答案不一致（62 规范化 '[60,)' vs 82 原样'50万以上'），不立规则；"交易金额分布"类 = 维度原始码 + `SUM(buy_amt)`/`SUM(sell_amt)` 分列两列，不合并、不译中文标签（train_4/57，详见 aliases.md）；"情况"类（盈亏情况等无筛选全量）= **逐客户明细** pty_id+全部指标列（end/bgn/in/out/pft）、order by pty_id（train_5/68：单值合计判错）；持仓明细/集中度类 = 按**原始持仓行**逐行判定与输出（不按 (pty_id,prdt_id) 跨账户 SUM 合并，nm/fc 双行各算一行、各自对总资产算占比）并 join dim_product 带 prdt_name 列（train_5/74——"不 join 姓名"仅适用客户名单，明细对象是产品时带名称，与 train_6/88 产品名单同源） | 全部 |
| 均值类分母按指标类型二分（用户确认，train_2 序号 39 + train_4 序号 65 答案裁决）：**资产类均值**（ads 属性 × aset 聚合，如各等级平均总资产）标准答案用 `LEFT JOIN` 事实表（日期条件放 ON 上）+ `COALESCE(…,0)`，把无事实记录客户按 0 计入分母（每等级分母=该等级全体客户数），**非 inner join 排除法**；实测银卡 151 人中 1 人、"空"65 人中 13 人无期末资产，两口径数值不同（train_3/40/41 复用成功）；**持有/交易类计数均值**（如平均持有产品种类数）反之用排除法：inner join 只计有记录客户（train_4/65：女性平均持有产品种类数 = 期末有持仓的 161 人得 7.8 判对，全体 182 人分母得 6.87 判错，6.87×182/161≈7.8 互验；舍入 round 1）；**驱动表按分组维度类型二分（用户裁决，2026-08-25，train_7/94 消解 39 vs 94 表面冲突）**：属性维度分组（客户等级/性别/学历等 ads 属性）→ ads 全体客户驱动 + LEFT JOIN 事实表 + COALESCE(0)（39/40/41 同型）；事实维度分组（持有科创板与否等由事实表判定的二分）→ **期末时点事实表客户全集驱动**（train_7/94：期末 aset 486 人全集，14 名无期末资产记录的 ads 客户不参与，非 ads 500 驱动；效率注：ads 500 驱动再双左连慢 ~20%，is_slower 实证） | ads_cust_info_d、dws_cust_aset_d、dwd_cust_hold_d、dwd_cust_tran_d |
| dim_branch 机构类计数按字段字面语义（用户确认，train_2 序号 18/19/20 三题裁决）："多少家营业部"=全表 `count(distinct org_id)`（312，含 26 分公司行）；"多少家分公司"=`count(distinct up_org_id)`（27，含表外"财富管理部"）；分布 `group by up_org_name` 全表 27 组不筛行类型——**不按 org_name 业务含义过滤**（详见 dim_branch.md） | dim_branch |
| 两时点对比**统计基数**（train_5/70 + train_6/84 综合规则）：以**题面语义基准时点**的客户全集为驱动（`select distinct pty_id`），另一端点 LEFT JOIN、缺失按资产 0 计，**不取两端点交集**——盈亏/情况类基准=期末 20260331 全集（train_5/68、train_6/84：交集 485 人 vs 答案 486 人，差 1 人落盈利 206 vs 205 判错）；流失/减少类基准=期初 20260101 全集（train_5/70：期初客户缺期末记录按 0 计入流失，答案 120 行 vs 交集 119 行，差 1 人 C000000000000295 期初 0.36 元）；单扫 aset 条件聚合写法比答案三扫快，可沿用 | dws_cust_aset_d、dws_cust_fin_d |
| 小名单驱动的题（先筛出少量客户再取其度量）**先 join 后聚合**，勿预聚合全量表再 join：15 名客户取 Q1 交易额，先聚合 tran 全量 385 组再 join 比答案"15 键 hash 探测后聚合"慢 ~3 倍（30.6 vs 10.0ms 实测，train_6/85）；预聚合全量仅在大名单（分组维度接近全量）时合理 | dwd_cust_tran_d、dws_cust_fin_d |
