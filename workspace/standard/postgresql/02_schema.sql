\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

CREATE TABLE IF NOT EXISTS dim_product (
    prdt_id varchar(12),
    prdt_name varchar(100),
    sor_prdt_id varchar(12),
    market_id varchar(50),
    prdt_type_id varchar(12),
    prdt_type_name varchar(40),
    up_prdt_type_id varchar(12),
    up_prdt_type_name varchar(40)
);

CREATE TABLE IF NOT EXISTS ads_cust_info_d (
    data_dt varchar(8),
    pty_id varchar(32),
    sor_pty_id varchar(32),
    cust_lvl_cd varchar(12),
    cust_status varchar(12),
    cust_type varchar(1),
    prov_name varchar(50),
    city_name varchar(50),
    birth_dt varchar(8),
    cust_age numeric(20,0),
    name varchar(40),
    gender_cd varchar(12),
    edu_cd varchar(32),
    prof_cd varchar(100),
    org_id varchar(100)
);

CREATE TABLE IF NOT EXISTS dws_cust_fin_d (
    data_dt varchar(8) NOT NULL,
    pty_id varchar(32) NOT NULL,
    sys_source varchar(20) NOT NULL,
    cash_in numeric(20,4),
    cash_out numeric(20,4),
    tran_in numeric(20,4),
    tran_out numeric(20,4),
    assign_in numeric(20,4),
    assign_out numeric(20,4)
);

CREATE TABLE IF NOT EXISTS dwd_cust_hold_d (
    data_dt varchar(8) NOT NULL,
    pty_id varchar(32) NOT NULL,
    prdt_id varchar(12) NOT NULL,
    sys_source varchar(20) NOT NULL,
    ccy varchar(12) NOT NULL,
    hold_cnt numeric(20,4),
    mkt_val numeric(20,4)
);

CREATE TABLE IF NOT EXISTS dwd_cust_tran_d (
    data_dt varchar(8) NOT NULL,
    pty_id varchar(32) NOT NULL,
    prdt_id varchar(12) NOT NULL,
    sys_source varchar(20) NOT NULL,
    ccy varchar(12) NOT NULL,
    buy_cnt integer,
    buy_mnt numeric(20,4),
    buy_rake numeric(20,4),
    buy_amt numeric(20,4),
    buy_fare numeric(20,4),
    sell_cnt integer,
    sell_mnt numeric(20,4),
    sell_rake numeric(20,4),
    sell_amt numeric(20,4),
    sell_fare numeric(20,4)
);

CREATE TABLE IF NOT EXISTS dws_cust_aset_d (
    data_dt varchar(8) NOT NULL,
    pty_id varchar(32) NOT NULL,
    nm_tot_aset numeric(20,4),
    nm_bal numeric(20,4),
    fc_pur_aset numeric(20,4),
    fc_bal numeric(20,4)
);

CREATE TABLE IF NOT EXISTS dim_public (
    code varchar(12) NOT NULL,
    code_type_id varchar(6) NOT NULL,
    describe varchar(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_branch (
    data_dt varchar(8) NOT NULL,
    org_id varchar(50) NOT NULL,
    org_name varchar(100) NOT NULL,
    up_org_id varchar(50) NOT NULL,
    up_org_name varchar(100) NOT NULL
);

COMMENT ON TABLE dim_product IS '产品属性维表';
COMMENT ON TABLE ads_cust_info_d IS '客户信息表';
COMMENT ON TABLE dws_cust_fin_d IS '客户资金流动日事实';
COMMENT ON TABLE dwd_cust_hold_d IS '客户持有产品日事实';
COMMENT ON TABLE dwd_cust_tran_d IS '客户交易类买卖日事实';
COMMENT ON TABLE dws_cust_aset_d IS '客户资产日汇总';
COMMENT ON TABLE dim_public IS '标准化编码字典表';
COMMENT ON TABLE dim_branch IS '营业部表';

DO $role$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ht_eval') THEN
        CREATE ROLE ht_eval LOGIN;
    END IF;
END
$role$;

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE ht_competition TO ht_eval;
GRANT USAGE ON SCHEMA public TO ht_eval;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ht_eval;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ht_eval;
ALTER ROLE ht_eval SET default_transaction_read_only = on;
ALTER ROLE ht_eval SET statement_timeout = '30s';

COMMIT;
