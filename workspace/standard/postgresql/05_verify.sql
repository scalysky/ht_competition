\set ON_ERROR_STOP on
\encoding UTF8

SELECT table_name, row_count
FROM (
    SELECT 1 AS sort_order, 'ads_cust_info_d'::text AS table_name, count(*) AS row_count FROM ads_cust_info_d
    UNION ALL SELECT 2, 'dim_branch', count(*) FROM dim_branch
    UNION ALL SELECT 3, 'dim_product', count(*) FROM dim_product
    UNION ALL SELECT 4, 'dim_public', count(*) FROM dim_public
    UNION ALL SELECT 5, 'dwd_cust_hold_d', count(*) FROM dwd_cust_hold_d
    UNION ALL SELECT 6, 'dwd_cust_tran_d', count(*) FROM dwd_cust_tran_d
    UNION ALL SELECT 7, 'dws_cust_aset_d', count(*) FROM dws_cust_aset_d
    UNION ALL SELECT 8, 'dws_cust_fin_d', count(*) FROM dws_cust_fin_d
) counts
ORDER BY sort_order;

SELECT current_database() AS database_name,
       pg_encoding_to_char(encoding) AS encoding
FROM pg_database
WHERE datname = current_database();

SELECT rolname,
       rolcanlogin,
       rolconfig
FROM pg_roles
WHERE rolname = 'ht_eval';
