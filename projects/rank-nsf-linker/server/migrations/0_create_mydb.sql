-- pgaudit only where Postgres preloads it (the dev config); the minimal deploy's Postgres doesn't
DO $$
BEGIN
    IF current_setting('shared_preload_libraries') LIKE '%pgaudit%' THEN
        CREATE EXTENSION IF NOT EXISTS pgaudit;
    END IF;
END
$$;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
SET pg_trgm.similarity_threshold = 0.8;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_database WHERE datname = 'rank-nsf-linker'
    ) THEN
        CREATE DATABASE "rank-nsf-linker";
    END IF;
END
$$;