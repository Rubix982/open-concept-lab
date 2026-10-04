-- Lookups by institution: classification, merge (repointing + FK checks on delete) and linking
-- scan these per university; without indexes that is a full award scan each time.
CREATE INDEX IF NOT EXISTS award_institution_idx ON award (institution);
CREATE INDEX IF NOT EXISTS award_performing_institution_idx ON award (performing_institution);
CREATE INDEX IF NOT EXISTS professors_affiliation_idx ON professors (affiliation);
CREATE INDEX IF NOT EXISTS professor_areas_affiliation_idx ON professor_areas (affiliation);
