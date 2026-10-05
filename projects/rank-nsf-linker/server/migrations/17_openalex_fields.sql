-- Fields beyond computer science: researchers come from OpenAlex ("Load OpenAlex Researchers"),
-- one area per OpenAlex field; venue 'oa:<field id>' is what their professor_areas rows carry.
INSERT INTO research_area_venues (area_group, area, area_name, venue) VALUES
  ('Sciences', 'physics', 'Physics and astronomy', 'oa:31'),
  ('Sciences', 'chemistry', 'Chemistry', 'oa:16'),
  ('Sciences', 'mathematics', 'Mathematics', 'oa:26'),
  ('Sciences', 'biochemistry', 'Biochemistry, genetics and molecular biology', 'oa:13'),
  ('Sciences', 'agbio', 'Agricultural and biological sciences', 'oa:11'),
  ('Sciences', 'earth', 'Earth and planetary sciences', 'oa:19'),
  ('Sciences', 'environment', 'Environmental science', 'oa:23'),
  ('Engineering', 'materials', 'Materials science', 'oa:25'),
  ('Engineering', 'engineering', 'Engineering', 'oa:22'),
  ('Engineering', 'chemeng', 'Chemical engineering', 'oa:15'),
  ('Engineering', 'energy', 'Energy', 'oa:21'),
  ('Medicine', 'medicine', 'Medicine', 'oa:27'),
  ('Medicine', 'neuroscience', 'Neuroscience', 'oa:28'),
  ('Medicine', 'immunology', 'Immunology and microbiology', 'oa:24')
ON CONFLICT (venue) DO UPDATE SET area_group = EXCLUDED.area_group, area = EXCLUDED.area, area_name = EXCLUDED.area_name;

-- Where a person comes from: 'csrankings' (verified computer science faculty) or 'openalex'
-- (researchers in other fields, selected by heuristics; not verified faculty).
ALTER TABLE professors ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'csrankings';
ALTER TABLE explorer_faculty ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'csrankings';
