DROP VIEW IF EXISTS university_faculty_view;

CREATE OR REPLACE VIEW university_faculty_view AS
SELECT
  u.institution,
  u.longitude,
  u.latitude,
  u.city,
  u.region,
  u.country,
  u.homepage,
  (
    SELECT JSON_AGG(
      JSONB_BUILD_OBJECT(
        'name', p2.name,
        'nsf_funding', (
          SELECT SUM(aw2.award_amount)
          FROM award aw2
          WHERE aw2.id IN (
            SELECT awpr2.award_id
            FROM award_pi_rel awpr2
            WHERE awpr2.investigator_id = p2.name
          )
        ),
        'awards_count', (
          SELECT COUNT(aw3.id)
          FROM award aw3
          WHERE aw3.id IN (
            SELECT awpr3.award_id
            FROM award_pi_rel awpr3
            WHERE awpr3.investigator_id = p2.name
          )
        ),
        'active_awards', (
          SELECT COUNT(*)
          FROM award aw4
          JOIN award_pi_rel awpr4 ON aw4.id = awpr4.award_id
          WHERE awpr4.investigator_id = p2.name
            AND aw4.award_expiry_date::date > CURRENT_DATE
        ),
        'research_areas', (
          SELECT ARRAY_AGG(DISTINCT pa.area)
          FROM professor_areas pa
          WHERE pa.name = p2.name
            AND pa.affiliation = p2.affiliation
        ),
        'sub_areas', (
          SELECT ARRAY_AGG(DISTINCT psa.area)
          FROM professor_areas psa
          WHERE psa.name = p2.name
            AND psa.affiliation = p2.affiliation
        ),
        'homepage', p2.homepage
      )
    )
    FROM professors p2
    LEFT JOIN award_pi_rel awpr ON p2.name = awpr.investigator_id
    LEFT JOIN award aw ON aw.id = awpr.award_id
      AND p2.affiliation = aw.institution
    WHERE p2.affiliation = u.institution
  ) AS faculty
FROM
  universities u;