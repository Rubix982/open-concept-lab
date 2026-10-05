-- Computer science researchers from OpenAlex, at universities CSRankings doesn't list (Pakistan's,
-- see scripts/openalex/extra_universities.py). One general area: CSRankings' finer areas need venues.
INSERT INTO research_area_venues (area_group, area, area_name, venue) VALUES
  ('Engineering', 'computing', 'Computer science (OpenAlex)', 'oa:17')
ON CONFLICT (venue) DO UPDATE SET area_group = EXCLUDED.area_group, area = EXCLUDED.area, area_name = EXCLUDED.area_name;
