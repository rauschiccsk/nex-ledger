#!/bin/bash
set -e

# Create test database alongside production database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE nex_ledger_test;
    GRANT ALL PRIVILEGES ON DATABASE nex_ledger_test TO $POSTGRES_USER;
EOSQL

echo "Test database 'nex_ledger_test' created successfully."
