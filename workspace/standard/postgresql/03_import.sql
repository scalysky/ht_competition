\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

DO $empty_check$
BEGIN
    IF EXISTS (SELECT 1 FROM dim_product LIMIT 1)
       OR EXISTS (SELECT 1 FROM ads_cust_info_d LIMIT 1)
       OR EXISTS (SELECT 1 FROM dws_cust_fin_d LIMIT 1)
       OR EXISTS (SELECT 1 FROM dwd_cust_hold_d LIMIT 1)
       OR EXISTS (SELECT 1 FROM dwd_cust_tran_d LIMIT 1)
       OR EXISTS (SELECT 1 FROM dws_cust_aset_d LIMIT 1)
       OR EXISTS (SELECT 1 FROM dim_public LIMIT 1)
       OR EXISTS (SELECT 1 FROM dim_branch LIMIT 1) THEN
        RAISE EXCEPTION 'Data already exists; import aborted to prevent duplicates';
    END IF;
END
$empty_check$;

\copy ads_cust_info_d (data_dt,pty_id,sor_pty_id,cust_lvl_cd,cust_status,cust_type,prov_name,city_name,birth_dt,cust_age,name,gender_cd,edu_cd,prof_cd,org_id) FROM 'C:/Code/Fin_tech_match/.pg_import_data/ads_cust_info_d_202606031625.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy dim_branch (data_dt,org_id,org_name,up_org_id,up_org_name) FROM 'C:/Code/Fin_tech_match/.pg_import_data/dim_branch_202606021048.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy dim_product (prdt_id,prdt_name,sor_prdt_id,market_id,prdt_type_id,prdt_type_name,up_prdt_type_id,up_prdt_type_name) FROM 'C:/Code/Fin_tech_match/.pg_import_data/dim_product_202606021049.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy dim_public (code,code_type_id,describe) FROM 'C:/Code/Fin_tech_match/.pg_import_data/dim_public_202606021050.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy dwd_cust_hold_d (data_dt,pty_id,prdt_id,sys_source,ccy,hold_cnt,mkt_val) FROM 'C:/Code/Fin_tech_match/.pg_import_data/dwd_cust_hold_d_202606021051.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy dwd_cust_tran_d (data_dt,pty_id,prdt_id,sys_source,ccy,buy_cnt,buy_mnt,buy_rake,buy_amt,buy_fare,sell_cnt,sell_mnt,sell_rake,sell_amt,sell_fare) FROM 'C:/Code/Fin_tech_match/.pg_import_data/dwd_cust_tran_d_202606021051.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy dws_cust_aset_d (data_dt,pty_id,nm_tot_aset,nm_bal,fc_pur_aset,fc_bal) FROM 'C:/Code/Fin_tech_match/.pg_import_data/dws_cust_aset_d_202606021051.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy dws_cust_fin_d (data_dt,pty_id,sys_source,cash_in,cash_out,tran_in,tran_out,assign_in,assign_out) FROM 'C:/Code/Fin_tech_match/.pg_import_data/dws_cust_fin_d_202606021050.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')

COMMIT;
ANALYZE;
