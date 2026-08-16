# ads_cust_info_d — 客户信息表

## 表描述

客户属性宽表，日快照。**本数据集仅含单一快照日 `20260531`，共 500 行 = 500 名客户**，粒度 `(data_dt, pty_id)` 唯一。（来源：数据推测，由行数与去重计数验证）

与事实表（aset/fin/tran/hold）的日期不对齐：事实表最晚到 `20260331`，本表是 `20260531` 的快照。按客户属性筛选历史事实时直接用 `pty_id` join，**不要加日期相等条件**。（来源：数据推测）

## 字段

| 字段 | 类型 | 说明 | 来源 |
|---|---|---|---|
| data_dt | varchar(8) | 日期，`YYYYMMDD` 字符串 | 用户提供 |
| pty_id | varchar(32) | 客户号，格式 `C000000000000001` | 用户提供 |
| sor_pty_id | varchar(32) | 经纪客户号，19 位，格式 `6666000000000000001` | 用户提供 |
| cust_lvl_cd | varchar(12) | 客户等级码，关联 `dim_public(code, code_type_id='100')`。实测取值 1000001–1000006 = 紫金理财钻石卡/白金卡/金卡/银卡卡/理财卡客户/空 | 用户提供 + 数据推测 |
| cust_status | varchar(12) | 账户状态码，关联 `dim_public(code, code_type_id='200')`。实测：2000001 正常（486 人）、2000004 销户（11 人）、2000005 休眠已确认（3 人） | 用户提供 + 数据推测 |
| cust_type | varchar(1) | 客户类型，实测全部为 `P`（推测=个人客户） | 用户提供 |
| prov_name | varchar(50) | 省份，实测如 `江苏省` | 用户提供 |
| city_name | varchar(50) | 城市，实测如 `南京市`、`苏州市` | 用户提供 |
| birth_dt | varchar(8) | 出生日期，`YYYYMMDD` 字符串 | 用户提供 |
| cust_age | numeric(20,0) | 年龄 | 用户提供 |
| name | varchar(40) | 姓名，已脱敏，如 `伟***` | 用户提供 |
| gender_cd | varchar(12) | 性别码，关联 `dim_public(code, code_type_id='500')`：5000002 男（318 人）、5000003 女（182 人） | 用户提供 + 数据推测 |
| edu_cd | varchar(32) | 学历码，关联 `dim_public(code, code_type_id='600')`：6000002 博士 ~ 6000008 初中及其以下、6000005 大专等 | 用户提供 + 数据推测 |
| prof_cd | varchar(100) | 职业类型编码，关联 `dim_public(code, code_type_id='700')`，本数据集实际出现 31 种取值（7000001 军人 ~ 7000058 其他专业技术人员） | 用户提供 + 数据推测 |
| org_id | varchar(100) | 所属营业部ID，格式 `XX00000049`，关联 `dim_branch(org_id)` | 用户提供 + 数据推测 |
