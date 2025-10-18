CREATE EXTENSION IF NOT EXISTS pgaudit;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_database WHERE datname = 'mydb'
    ) THEN
        CREATE DATABASE mydb;
    END IF;
END
$$;