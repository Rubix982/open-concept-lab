CREATE TABLE IF NOT EXISTS organizations (LIKE universities INCLUDING ALL);

-- Keep column order identical to universities: rows are copied with SELECT *
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS institution_type TEXT;
