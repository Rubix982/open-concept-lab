-- What the explorer_grants Qdrant collection holds (grant_search.go): one row per grant embedded.
CREATE TABLE IF NOT EXISTS explorer_grants_embedded (
    id   UUID PRIMARY KEY,
    hash TEXT NOT NULL
);
