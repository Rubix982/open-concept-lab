-- A university's grants (the "Grants held here" list on its page): found by index, not by scanning
-- all 1.1M grants.
CREATE INDEX IF NOT EXISTS explorer_grants_university_idx ON explorer_grants (university_id);
