ALTER TABLE labs ADD COLUMN IF NOT EXISTS lab TEXT PRIMARY KEY;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'labs_lab_universities_institution_fk'
  ) THEN
    ALTER TABLE labs
      ADD CONSTRAINT labs_lab_universities_institution_fk FOREIGN KEY (lab)
      REFERENCES universities (institution) ON DELETE SET NULL;
  END IF;
END
$$;
