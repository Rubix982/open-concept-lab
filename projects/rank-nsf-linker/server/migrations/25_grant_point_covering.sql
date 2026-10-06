-- The point-id index carries funder and id, so mapping Qdrant hits to grants reads only the index
-- (3,000 lookups into the 2.4 GB table took ~3 s when it wasn't cached).
DROP INDEX IF EXISTS explorer_grants_point_idx;
CREATE INDEX IF NOT EXISTS explorer_grants_point_cover_idx
  ON explorer_grants ((md5(funder || '|' || id)::uuid)) INCLUDE (funder, id);
