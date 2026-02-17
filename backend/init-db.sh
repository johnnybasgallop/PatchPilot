#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE airflow' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')\gexec
    SELECT 'CREATE DATABASE patch_pilot' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'patch_pilot')\gexec
EOSQL