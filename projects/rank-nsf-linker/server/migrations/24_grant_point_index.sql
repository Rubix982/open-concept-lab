-- A grant's Qdrant point id is md5(funder|id) (grant_search.go): searches fetch only point ids from
-- Qdrant (payloads are read from disk: 1.9 s for 5,000 hits, 0.36 s without) and find the grants here.
CREATE INDEX IF NOT EXISTS explorer_grants_point_idx ON explorer_grants ((md5(funder || '|' || id)::uuid));
