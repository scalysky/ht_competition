# questions.md — text2sql 模糊点记录（累积）

## train_1 批次（2026-08-23，已消化）

来源：`dataset/split/train_1/questions.md`（9 序号 + 跨题共性），经 answer 对照与 db-access 实测全部裁决，消化去向如下。原始记录全文保留在来源文件，不删除。

| 条目 | 裁决 | 消化去向 | 状态 |
|---|---|---|---|
| Q2 "资产"口径与时点 | 期末 20260331 单日时点 SUM，非日均 | aliases.md + dws_cust_aset_d.md | 已消化 |
| Q2 年龄分段空档 | 第 4 段 `[60,)` 含 60 岁 | （口径偏好，无需表级修正） | 已消化 |
| Q3 盈亏定义 | 期末−期初+期间净流出（fin 六字段）；比亚迪=期末单日、精确匹配、SUM>1000 | aliases.md + dws_cust_fin_d.md | 已消化 |
| Q3/Q6 标准答案 SQL 自带 bug（符号笔误 / aset×tran 行膨胀） | 不复刻，保持语义正确 | correlation.md 注意事项（输出格式条） | 已消化 |
| Q4 输出粒度 | 分公司→营业部→省份→城市→客户数 | correlation.md 注意事项（输出格式条） | 已消化 |
| Q6 日均资产 | `SUM/90`（与 AVG(逐日) 集合等价，212 人实测互证） | aliases.md + dws_cust_aset_d.md | 已消化 |
| Q6/Q7 交易量口径与 nm/fc 双记录去重之争 | 双边金额直接 SUM **不去重、不滤 ccy**（用户确认，向答案对齐）；双记录数据现象确证为重复记账 | aliases.md + dwd_cust_tran_d.md + correlation.md | 已消化 |
| Q7 科创板识别 / 日期边界 | 二级分类精确匹配；between 含两端 | aliases.md + dim_product.md | 已消化 |
| Q11/12/13/15 客户状态与输出格式 | 全体客户无状态过滤；均值 `ROUND(x,1)`；排序 `ORDER BY 度量 DESC` | correlation.md 注意事项 | 已消化 |
| 客户等级码 1000006（"空"） | 作独立等级输出不剔除 | dim_public.md 别名节 | 已消化 |
| 金额单位 | 阈值按元（300000/100000/250000/1000） | aliases.md（随口径条目体现） | 已消化 |

## train_2 批次（2026-08-24，已消化）

来源：`dataset/split/train_2/questions.md`（9 序号 + 跨题共性，5/9 判对），已对照 answer.json 与 compare.json 全部裁决并经 db-access 实测。原始记录全文保留在来源文件，不删除。

| 条目 | 裁决 | 消化去向 | 状态 |
|---|---|---|---|
| Q18/19/20 dim_branch 混装结构与机构计数口径 | 机构类计数按字段字面：全表 org_id=312、up_org_id 去重=27（含表外"财富管理部"）、group by 全表 27 组不筛行——不按 org_name 业务含义过滤 | dim_branch.md（表描述重写）+ correlation.md 注意事项（新增字面计数条） | 已消化 |
| Q39 均值类分母 | left join + coalesce(0) 把无期末资产客户按 0 计入分母（每等级分母=全体客户数），非 inner join 排除法 | correlation.md 注意事项（新增均值分母条） | 已消化 |
| Q39 舍入位数 | 资产均值 round 2 位（年龄均值 round 1 位、合计不 round，按指标类型区分） | correlation.md 注意事项（输出格式条更新） | 已消化 |
| Q23 唯一键计数 | prdt_id 唯一已实测，count(*) 即可；COUNT(DISTINCT) 在 33 万行上慢 5.9 倍 | correlation.md 注意事项（客户数条补反向规则） | 已消化 |
| Q29 排序例外 | 分布类主流度量 DESC，存在维度升序例外（order by ccy）；值集等价即判对 | correlation.md 注意事项（输出格式条更新） | 已消化 |
| Q16/21/37 正确题口径复核 | round 1 / 全体客户 / 码全命中时 inner=left / describe 明文输出——均与既有知识库一致 | 无需变更（复核通过） | 已消化 |
| nm/fc 双记录汇总口径（用户再次裁决"按照知识库的来"） | 按知识库：原始行直接 SUM、不去重、不滤 ccy，维持不变 | 无知识库变更（train_1 结论继续有效，train_3~7 直接沿用） | 已消化 |

## train_3 批次（2026-08-24，已消化）

来源：`dataset/split/train_3/questions.md`（9 序号 + 跨题共性，7/9 判对），已对照 answer.json 与 compare.json 全部裁决并经 db-access 双方 SQL 实测。原始记录全文保留在来源文件，不删除。

| 条目 | 裁决 | 消化去向 | 状态 |
|---|---|---|---|
| Q43/Q51 滤币种规则适用面 | **以题面为准**：明示币种才滤（51 ccy='2'），未提币种不滤、全币种 SUM、客户数同口径（43 判错教训） | correlation.md（ccy 条重写）+ dwd_cust_hold_d.md（mkt_val 字段说明，来源升级用户确认） | 已消化 |
| Q42 名单类输出列 | 客户名单/客户及其指标 = 仅 pty_id 一列（+可选度量列），**不 join ads 取姓名**（pty_id 集合本身全对，仅列形态判错） | correlation.md（输出格式条补名单类规则） | 已消化 |
| Q45 机构字面计数 vs 客户侧统计边界 | 数机构行按字面全表（train_2 18/19/20）；数客户从客户侧 inner join、零客户机构不输出（实测/答案均 10 组） | correlation.md（dim_branch 桥接条补边界）+ dim_branch.md（字面计数节补边界） | 已消化 |
| Q54 占比输出格式 | 百分数 `ROUND(x*100.0/…,2)`（15/3.00 全同，判对） | correlation.md（输出格式条补占比规则） | 已消化 |
| Q40/41 均值分母口径复用 | train_2 序号 39 裁决（LEFT JOIN+COALESCE(0)、分母=全体客户）在性别/学历两题复用成功，数值全同 | 无需变更（复核通过） | 已消化 |
| Q40/46 排序维度升序例外 | 答案 `order by gender/profession` 维度升序，值集等价仍判对——维度升序例外清单新增 2 例 | correlation.md（输出格式条更新例外清单） | 已消化 |
| Q49 Q1 边界与"空"等级 | between 含两端、1000006"空"独立等级输出——均与既有知识一致 | 无需变更（复核通过） | 已消化 |
| 答案习惯带单快照日期条件 | 标准答案多处带 `where a.data_dt='20260531'`，单快照下等价、带上无害 | correlation.md（输出格式条补记） | 已消化 |
| 效率教训 | 为非必要输出列（姓名）多 join 一张表是结构性绕弯（42 is_slower=true）；码值过滤优于 join 码表按明文过滤（46/54 略快） | （写法偏好，随 42 条目体现在名单规则中） | 已消化 |

## train_4 批次（2026-08-24，已消化）

来源：`dataset/split/train_4/questions.md`（9 序号 + 跨题共性，裁决全文在来源文件），已对照 answer.json 与 compare.json 全部裁决（4/9 判对：56/58/61/64）并经 db-access 双方 SQL 实测互验。原始记录全文保留在来源文件，不删除。

| 条目 | 裁决 | 消化去向 | 状态 |
|---|---|---|---|
| 55 "各城市"输出列 | 省+市双维度列（prov_name, city_name, cnt, avg_age）；数值全同但缺省份列判错；排序 cnt desc+维度次级键 | correlation.md（输出格式条补地理双列） | 已消化 |
| 56 "持有产品数量"与并列 | COUNT(DISTINCT prdt_id) 正确；top-N 并列加次级键 `order by 度量 desc, pty_id`（第10/11名并列 53 分，pty_id 小者优先） | correlation.md（输出格式条补次级键） | 已消化 |
| 57 "交易金额分布" | 买/卖分列两列 `SUM(buy_amt)`/`SUM(sell_amt)`、维度原始码不译中文（合并+中文标签判错）；双边合计、不滤 ccy、原始行 SUM、between 含两端维持 | aliases.md + dwd_cust_tran_d.md（"交易金额分布"条双写）+ correlation.md 输出格式条 | 已消化 |
| 58 "100万"与名单列 | 全对（1,000,000 元、pty_id+度量列、DESC）；aset 期末无 NULL 字段，答案 coalesce 写法与直接相加等价 | 无需变更（复核通过） | 已消化 |
| 60 营业部分组粒度 | GROUP BY org_name 单列（脱敏同名字面合并：28 org_id→15 org_name，南京 9 行之和=答案值互验）；按 org_id 防同名合并假设错误；零资产客户 LEFT JOIN+COALESCE(0) 计入其营业部 | dim_branch.md（新增营业部聚合节）+ correlation.md（营业部桥接条补分组规则） | 已消化 |
| 61 "招商银行A股"定位 | prdt_name+prdt_type_name='A股' 圈定正确（同名多义：A股 600036 / H股 03968 / 理财债券同名多行）；不滤 ccy、LIMIT 不足额返回全部持有人维持 | dim_product.md（别名节补"股票同名消歧"条） | 已消化 |
| 62 年龄段标签 | 分档边界正确（[60,) 含 60）；标签须用区间记号 '[60,)'，意译"60以上"判错（train_1 同款佐证） | correlation.md（输出格式条补标签规则） | 已消化 |
| 64 fc 交易判定 | EXISTS 与 CTE DISTINCT+JOIN 等价全对（58.8=40 人）；ROUND(x,1) 单列维持 | 无需变更（复核通过） | 已消化 |
| 65 均值分母与舍入 | 分母=inner join 只计有期末持仓的 161 人（7.8 判对，全体 182 人得 6.87 判错，6.87×182/161≈7.8 互验）；train_2/39 全体分母规则适用面收窄至资产类均值；舍入 round 1 | correlation.md（均值分母条改写为按指标类型二分） | 已消化 |
| 跨题共性 | 客户状态/ads 日期条件/不滤 ccy/名单输出列 4 项与既有知识一致维持；维度升序例外 +2 例（57 sys_source、62 标签，累计 5 例） | correlation.md（输出格式条例外清单更新） | 已消化 |

## train_5 批次（2026-08-24，已消化）

来源：`dataset/split/train_5/questions.md`（9 序号 + 跨题共性，处置与裁决全文在来源文件，各节已打 √）。默认不中途追问，全部自行拍定并逐条声明假设；取值经 db-access 只读抽样实测，9 条 SQL 均经 EXPLAIN 校验（未取数）。**2026-08-24 已对照 answer.json 完成裁决：4/9 判对（66/72/73/77）、5/9 判错（68 输出粒度=逐客户明细、69 各月口径=月内全量快照 SUM、70 行集=期初客户 LEFT JOIN 缺期末按 0、74 持仓明细=原始行+prdt_name、75 买入=buy_amt>0/持有不滤 hold_cnt/双维度列）；EXPLAIN ANALYZE 实测 9 题我方全部不慢于答案（持平 3、更快 6）；75 差异归因经三变量分解实验精确复现（buy_amt+不滤份额=830/302 即答案）。66/70/72 三个无检验点事项经用户裁决（top-N 固定行数、边界词不含端点+区间衔接优先）一并消化。**

| 条目 | 处置（自行假设） | 涉及表与字段 | 状态 |
|---|---|---|---|
| 66 top-N 并列与输出列 | LIMIT 10 + `order by 度量 desc, pty_id`（train_4/56 先例）；名单类 pty_id+度量列、不 round | dws_cust_aset_d | 已消化 |
| 68 "全体客户盈亏"输出粒度（**最大风险点**） | 单值合计——"全体客户"整体主语、无分组维度无筛选，名单类题型惯例均带筛选条件 | dws_cust_aset_d × dws_cust_fin_d | 已消化 |
| 69 各月总资产取数 | 月末单日时点（20260131/20260228/20260331 实测齐，aset 覆盖全部日历日 90 天）；月份原始码 '202601'；月份升序 | dws_cust_aset_d | 已消化 |
| 70 "减少10%以上"边界 | 含边界（≥10% → 期末≤期初×0.9，"[60,) 含 60"同源"以上"语义）；输出 pty_id+期初+期末、按降幅比例 desc + pty_id；两端点 inner join（各 486 人、期初无零值，除法安全） | dws_cust_aset_d | 已消化 |
| 72 窗口并列取法 | RANK()（标准竞赛排名）+ rk≤20 并列可超额（题面明示"含并列名次"）；输出 pty_id+总资产+名次 | dws_cust_aset_d | 已消化 |
| 73 均值分母/等级标签/舍入/排序 | 分母=交易客户数（train_4/65 排除法）；双边金额原始行 SUM 不去重不滤 ccy；等级 join dim_public 输出明文（train_4/65 实证答案 join 码表）；金额 round 2、天数 round 1（无先例自拍）；维度升序（40/46 同型） | dwd_cust_tran_d × ads_cust_info_d × dim_public | 已消化 |
| 74 集中度分子与输出格式 | (pty_id,prdt_id) 跨账户 SUM(mkt_val)（44 组 nm+fc 双行实测）；分母 nm_tot_aset+fc_pur_aset；占比百分数 round 2、"超过"=严格 >；明细 5 列按占比 desc；22 行零份额残留 mkt_val=0 不影响 | dwd_cust_hold_d × dws_cust_aset_d | 已消化 |
| 75 买入/持有判据 | buy_cnt>0（15459 行纯卖出行实测，55 行 cnt=0 但 amt>0 怪行按 cnt 字面拍定）；hold_cnt>0（22 行清仓残留实测）；一级 up_prdt_type_name='股票' 行上直取（16 个二级分类实测）；(pty_id,prdt_id) 配对、两计数均 DISTINCT；产品数 desc | dwd_cust_tran_d × dwd_cust_hold_d × dim_product | 已消化 |
| 77 净流入方向与账户范围 | 净流入=in 三项−out 三项（题面括号一一对应）；不滤 sys_source；pty_id+度量、desc+pty_id、LIMIT 10、不 round；fin 六字段无 NULL 实测 | dws_cust_fin_d | 已消化 |
| 跨题共性 | 全体客户不滤状态、不滤 ccy、between 含两端、ads 带 20260531、名单金额不 round——均沿用既有知识；fin/tran 起日 20260105 的覆盖限制在 68/77 按全表计 | — | 已消化 |

消化去向（2026-08-24 kb-refine，train_6 批次先行消化后本批次跟进，两处交叉条目已合并）：

| 条目 | 消化去向 |
|---|---|
| 66/72 top-N 固定行数（用户裁决：优先 LIMIT 固定行数、并列不扩展，除非用户显式说明或日后改规则；66 同 72；次级键保留作并列时取法确定性） | correlation.md（输出格式条 top-N 规则更新） |
| 70 边界语义（用户裁决：区间分段题优先保证区间无缝衔接——train_1 [60,) 含 60 属衔接例；孤立存在的 < / <= 严格按文字判断，中文"以上/以下"**不含端点**，train_5/70 答案字面 < 佐证） | aliases.md（"以上/以下（边界词）"条，通用） |
| 68 "情况"类=逐客户明细（pty_id+全部指标列、order by pty_id，非单值合计） | aliases.md（"盈亏情况/XX情况类"条）+ correlation.md（输出格式条） |
| 69 各月趋势=月内全量快照 SUM（非月末时点、非日均） | aliases.md + dws_cust_aset_d.md（"各月/月度趋势"条，双写）+ correlation.md（口径偏好条补记） |
| 70 两时点对比=期初集 LEFT JOIN 缺期末按 0（流失类） | correlation.md（与 train_6/84 盈亏基数条合并为"两时点对比统计基数"统一条）+ dws_cust_aset_d.md（同步改写） |
| 73 均值分母=交易客户数复用成功、等级明文输出、金额 round 2 / 天数 round 1 | 无需变更（复核通过，train_4/65 排除法规则适用面再证） |
| 74 持仓明细=原始行逐行判定+prdt_name（不按 (pty_id,prdt_id) 合并） | dwd_cust_hold_d.md（"持仓明细/集中度"条）+ correlation.md（输出格式条，与 train_6/88 产品名单同源并入） |
| 75 买入=buy_amt>0 / 持有不滤 hold_cnt=0 | aliases.md + dwd_cust_tran_d.md（"买入过"条，双写）、dwd_cust_hold_d.md（"仍持有"条） |
| 77 判对（净流入=in−out、不滤 sys_source、LIMIT 10） | 无需变更（复核通过） |
| 跨题共性（不滤状态/ccy、between 含两端、ads 20260531、名单不 round） | 无需变更（与既有知识一致，维持） |

## train_6 批次（2026-08-24，已消化）

来源：`dataset/split/train_6/questions.md`（9 序号逐题记录 + 跨题共性，裁决全文见来源文件）。已对照 answer.json 与 compare.json 全部裁决（4/9 判对：78/79/80/85）并经 db-access 双方 SQL 实测互验。原始记录全文保留在来源文件，不删除。

| 条目 | 裁决 | 消化去向 | 状态 |
|---|---|---|---|
| 78 分公司三指标 | 双边交易额 + COALESCE(0) 计零 + inner join 上卷 up_org_name + 按期末资产 DESC，10 行值集全同判对 | 无需变更（复核通过，口径与既有知识一致） | 已消化 |
| 79 佣金前10 | `SUM(buy_rake)+SUM(sell_rake)` 题面明示；pty_id+度量列；无并列实例，次级键规则未受检验（无害保留） | 无需变更（复核通过） | 已消化 |
| 80 零交易客户归入"交易金额不足1万" | **含**：left join + coalesce(0)（12 名零交易富客户入选，pty_id 14 人集合全同判对）；pty_id-only 合法、度量列可选 | correlation.md（名单类二分条：客户名单规则再证） | 已消化 |
| 82 分层标签 | 边界正确（10万整归中档、50万整归上档）、两端点交集基数 485 人正确、计数矩阵全同——**仅标签文本判错**：答案 '<10万'/'[10万,50万)'/'50万以上'（带万贴题面），我的纯数字区间记号错。**标签量纲贴题面**为可统一规则；末档"X以上"两答案批间不一致（62 vs 82），**不立规则**（用户确认：能统一则统一，不能统一就算了）；段数照抄题面 | correlation.md（输出格式条分档段数与标签重写）+ aliases.md（分档/分层标签条） | 已消化 |
| 83 年龄分档段数 | 答案三段 '<30'/'[30,50)'/'[50,)'，我按 train_4/62 拍四段判错（9 vs 14 行）。**题面明示分档则照抄（实例全一致）；未明示则盲拍、不锚定先例**（用户确认：83 的三段不复刻，孤例不当先例）——批间不可消解风险如实记录 | correlation.md（输出格式条分档段数与标签重写）+ aliases.md（分档/分层标签条） | 已消化 |
| 84 盈亏统计基数 | **基数=期末 20260331 有资产记录客户全集 486 人、期初缺失按 0**，不取两端点交集 485（差 1 人落盈利 206 vs 205 判错）；公式/无流水净流出 0/=0 持平均对；单扫条件聚合写法比答案三扫快可沿用 | dws_cust_aset_d.md（盈亏统计基数条）+ dws_cust_fin_d.md（盈亏条补基数）+ correlation.md（新增基数条） | 已消化 |
| 85 "单日超50万"口径 | 行级 `cash_in>500000`（与客户单日合计实测同人，答案写法为行级）；判对。**效率教训 is_slower=true**：小名单驱动先 join 后聚合，预聚合全量再 join 慢 ~3 倍（30.6 vs 10.0ms） | dws_cust_fin_d.md（大额现金转入条）+ correlation.md（新增小名单条） | 已消化 |
| 87 占比题输出形态 | 判错两点：①"数量及占比"类**带分母列 cust_cnt**（缺列判错，train_4/55 同源）；②**HAVING 过滤零分子组**只输出 5 行有高价值客户的营业部（我含零组 15 行）。分母=营业部全体客户、org_name 分组、ROUND 百分数均对 | correlation.md（输出格式条占比规则补全） | 已消化 |
| 88 产品名单输出列 | **产品名单要 join dim_product 输出 prdt_name+prdt_type_name（二级分类名）并按其分组**+持有客户数+市值，仅 prdt_id 判错；"名单不 join 属性"只适用客户名单；不滤 ccy、COUNT(DISTINCT pty_id) 对；不 join 快 4.4 倍但形态错——形态优先 | correlation.md（名单类二分条）+ aliases.md（名单类输出列二分条）+ dim_product.md / dwd_cust_hold_d.md（产品名单展示条，双写） | 已消化 |

## train_7 批次（2026-08-25，已消化）

来源：`dataset/split/train_7/questions.md`（9 序号逐题记录 + 跨题共性，裁决全文见来源文件）。已对照 answer.json 完成裁决（4/9 判对：91/92/95/96）并经 db-access 双方 SQL 实测（结果集比对 + EXPLAIN ANALYZE 计时，compare.json 已产出）。原始记录全文保留在来源文件，不删除。**残留疑问经用户三项裁决（2026-08-25）：①单实例支撑的规则暂不入库（93 交集基数、97 full join 基数、97 输出列全集、94 对比类计数列）；②39 vs 94 表面冲突按"驱动表随分组维度类型二分"调和并入库；③舍入优先级：题面明示照抄、未明示优先 round，消解 39 vs 90 批间冲突。**

| 条目 | 裁决 | 消化去向 | 状态 |
|---|---|---|---|
| 89 比值精度 | 成员与其余 3 列全同，唯一判错点 = 比值 round 2（我 round 4）；单边 buy_amt、期末分母、nullif 防护均对 | correlation.md（输出格式条：合计/比值/比率 round 2 + 舍入优先级） | 已消化 |
| 90 月度合计舍入 | 环比值全同，唯一判错点 = tot_aset 也 round 2；月内全量 SUM、全体合计粒度、首月 NULL 保留均对；与 train_2/39"合计不 round"冲突经用户裁决消解（未明示优先 round，39 为历史例外） | correlation.md（输出格式条舍入优先级重写） | 已消化 |
| 91 fc 画像 | 5 行值集全同判对：fc 行存在判据、LEFT JOIN+COALESCE(0) 资产均值、等级明文、round 1/2 全对；cust_lvl_cd 维度升序值集等价 | correlation.md（维度升序例外清单 +1 例）；其余无需变更（复核通过） | 已消化 |
| 92 港币等级分布 | 3 行完全一致判对：题面明示币种才滤 ccy='2'、持有=行存在、三列输出、cnt desc+维度次级键 | 无需变更（复核通过） | 已消化 |
| 93 对称三分类基数 | 判错根源：答案 inner join 两端交集 448 人（178/128/142），我拍并集 461 人（多 6 新增+7 清仓）。裁决事实：对称三分类取交集——但**单实例，用户裁决暂不入库**，仅存来源文件 | 不入库（train_7/questions.md 裁决记录） | 已消化（记录在案） |
| 94 二分对比基数 | 判错两点：基数=期末 aset 486 全集（非 ads 500，14 名无期末资产客户不参与）、带 cust_cnt 列。前者经用户裁决以"驱动表随分组维度类型二分"调和入库；后者（对比类默认带计数列）**单实例暂不入库** | correlation.md（均值分母条补驱动表二分规则+效率注）；计数列不入库 | 已消化 |
| 95 高净值持仓偏好 | 10 行完全一致判对：严格 >100 万、双边不滤 ccy、一级分类 SUM(mkt_val)、组升序+市值 desc 全对 | 无需变更（复核通过） | 已消化 |
| 96 日均+交易 top10 | 成员与 tran_amt 全同判对：SUM/90>30 万严格、双边、LEFT JOIN 兜底、pty_id+度量列合法（度量列可选再证） | 无需变更（复核通过） | 已消化 |
| 97 综合排名基数 | 判错根源：答案 full join 487 全集、双向缺失按 0（零佣金者 rake_rank 居尾参与资产排名），aset_rank 整体偏移 1 位；成员 20 人全同。RANK()、次级键、LIMIT 20 并列实证均对——但 full join 基数**单实例暂不入库**；输出列全集归因为推测亦不入库 | 不入库（train_7/questions.md 裁决记录） | 已消化（记录在案） |
| 效率 | 仅 94 is_slower=true：事实维度二分题从期末事实表单边驱动优于 ads 500 驱动再双左连（~+20%）；97 我方 inner join 略快于答案 full join 但口径错，效率让位于正确性 | correlation.md（均值分母条驱动表规则内附效率注） | 已消化 |
| 跨题共性 | 基数规则全景（期末全集/期初全集/交集/full join 全集各有题型）单实例为主不入库；round 优先级、驱动表二分两项入库；名单度量列可选、ccy、双边、边界词等既有规则再证 | correlation.md 两处；其余无需变更 | 已消化 |
