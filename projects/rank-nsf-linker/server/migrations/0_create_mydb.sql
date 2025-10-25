CREATE EXTENSION IF NOT EXISTS pgaudit;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
SET pg_trgm.similarity_threshold = 0.8;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_database WHERE datname = 'mydb'
    ) THEN
        CREATE DATABASE mydb;
    END IF;
END
$$;