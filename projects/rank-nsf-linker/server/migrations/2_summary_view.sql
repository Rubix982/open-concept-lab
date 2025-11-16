DROP VIEW IF EXISTS university_summary_view;

CREATE 
OR REPLACE VIEW university_summary_view AS 
SELECT 
  u.institution as institution, 
  u.longitude as longitude, 
  u.latitude as latitude, 
  u.city as city, 
  u.region as region, 
  u.country as country, 
  COALESCE(CASE 
    WHEN u.homepage LIKE 'https://%' THEN u.homepage
    ELSE 'https://' || u.homepage
  END, '') AS homepage, 
  JSONB_BUILD_OBJECT (
    'total_faculty', 
    COUNT(p.name), 
    'total_funding', 
    COALESCE(SUM(a.award_amount), 0), 
    'award_count', 
    COUNT(a.id), 
    'active_awards', 
    COALESCE(SUM(
      CASE WHEN a.award_expiry_date :: date > CURRENT_DATE THEN 1 ELSE 0 END
    ), 0)
  ) as stats, 
  COALESCE(
    (
      SELECT 
        JSONB_OBJECT_AGG(area, area_count) 
      FROM 
        (
          SELECT 
            pf.area, 
            COUNT(*) AS area_count 
          FROM 
            professor_areas pf 
          WHERE 
            pf.affiliation = u.institution 
          GROUP BY 
            pf.area
        ) area_counts
    ),
    '{}'::jsonb
  ) AS research_areas
FROM 
  universities u 
  LEFT JOIN professors p ON u.institution = p.affiliation 
  LEFT JOIN award a ON u.institution = a.institution 
  LEFT JOIN professor_areas pf ON pf.name = p.name 
  AND pf.affiliation = p.affiliation 
WHERE
  LOWER(u.institution) LIKE '%college%'
  OR LOWER(u.institution) LIKE '%university%'
  OR LOWER(u.institution) LIKE '%institute%'
GROUP BY 
  u.institution
ORDER BY 
  u.institution ASC;
