\set ON_ERROR_STOP on
\encoding UTF8

SELECT format(
    'CREATE DATABASE %I WITH ENCODING %L TEMPLATE template0',
    'ht_competition',
    'UTF8'
)
WHERE NOT EXISTS (
    SELECT 1 FROM pg_database WHERE datname = 'ht_competition'
)
\gexec
