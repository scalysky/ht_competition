# dws_cust_aset_d — 客户资产日汇总

## 表描述
客户资产按"客户号 + 日期"的每日汇总事实表，记录普通账户与信用账户的资产/现金规模。（来源：用户提供，来自 `表描述.sql` 的 COMMENT）

实测 `data_dt` 范围 `20260101`~`20260331`（2026 年一季度），共 487 个客户、43684 行；**本表无 `sys_source` 字段**，不区分普通/信用以外的系统来源（仅用不同金额列区分账户类型）。

## 字段
| 字段 | 类型 | 含义 | 来源 | 备注 |
|---|---|---|---|---|
| data_dt | varchar(8) | 日期 | 用户提供 | 字符型 YYYYMMDD |
| pty_id | varchar(32) | 客户号 | 用户提供 | 关联 ads 等表 |
| nm_tot_aset | numeric(20,4) | 普通账户总资产 | 用户提供 | |
| nm_bal | numeric(20,4) | 普通账户现金资产 | 用户提供 | |
| fc_pur_aset | numeric(20,4) | 信用账户净资产 | 用户提供 | |
| fc_bal | numeric(20,4) | 信用账户现金资产 | 用户提供 | |

## 关系
- `pty_id` ↔ `ads_cust_info_d` 及各事实表的 `pty_id`（关系状态：推测）。
- 与同含 `sys_source` 的事实表（fin/hold/tran）按 `pty_id`+`data_dt` 关联时，**本表无 sys_source 维度**，需注意汇总口径差异（见 correlation.md 注意事项）。

## 待确认
- 资产金额单位/币种（字段无 ccy，推测为人民币元）。
