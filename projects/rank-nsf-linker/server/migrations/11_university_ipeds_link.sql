-- IPEDS UNITID of a US university row; set by the "Link IPEDS Institutions" step.
ALTER TABLE universities ADD COLUMN IF NOT EXISTS ipeds_unitid INTEGER;
CREATE INDEX IF NOT EXISTS universities_ipeds_unitid_idx ON universities (ipeds_unitid);
