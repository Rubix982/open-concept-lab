-- More OpenAlex fields, and their subfields as research areas (scripts/openalex/fields.py).
-- area_field: the OpenAlex field a subfield area belongs to (NULL for CSRankings areas and whole fields).
ALTER TABLE research_area_venues ADD COLUMN IF NOT EXISTS area_field TEXT;
INSERT INTO research_area_venues (area_group, area, area_name, venue) VALUES
  ('Medicine', 'nursing', 'Nursing', 'oa:29'),
  ('Medicine', 'pharmacology', 'Pharmacology, toxicology and pharmaceutics', 'oa:30'),
  ('Medicine', 'veterinary', 'Veterinary', 'oa:34'),
  ('Medicine', 'dentistry', 'Dentistry', 'oa:35'),
  ('Medicine', 'health', 'Health professions', 'oa:36'),
  ('Social sciences & humanities', 'psychology', 'Psychology', 'oa:32'),
  ('Social sciences & humanities', 'economics', 'Economics, econometrics and finance', 'oa:20'),
  ('Social sciences & humanities', 'social', 'Social sciences', 'oa:33'),
  ('Social sciences & humanities', 'business', 'Business, management and accounting', 'oa:14'),
  ('Social sciences & humanities', 'decision', 'Decision sciences', 'oa:18'),
  ('Social sciences & humanities', 'arts', 'Arts and humanities', 'oa:12')
ON CONFLICT (venue) DO UPDATE SET area_group = EXCLUDED.area_group, area = EXCLUDED.area, area_name = EXCLUDED.area_name;
