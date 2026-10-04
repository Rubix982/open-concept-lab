package main

import (
	"fmt"

	colly "github.com/gocolly/colly/v2"
)

// buildExplorerSQL precomputes what the student-facing explorer reads:
//   - explorer_faculty: one row per CSRankings professor with recent publications — their
//     research areas (last 10 years) and NSF award counts / active funding.
//   - explorer_work_docs: a full-text document per NSF award and recent paper, for goal matching.
//   - explorer_universities: one row per university with such faculty — IPEDS facts
//     (R1/R2, graduate tuition and enrollment) and faculty counts per area.
const buildExplorerSQL = `
TRUNCATE explorer_faculty, explorer_universities, explorer_work_docs;

CREATE TEMP TABLE x_pubs ON COMMIT DROP AS
SELECT pa.name, v.area, sum(pa.count) AS pubs
FROM professor_areas pa JOIN research_area_venues v ON v.venue = pa.area
WHERE pa.year >= extract(year FROM current_date)::int - 10
GROUP BY pa.name, v.area;

-- A professor's university: CSRankings' current affiliation, else their most recent publication affiliation.
CREATE TEMP TABLE x_aff ON COMMIT DROP AS
SELECT DISTINCT ON (pa.name) pa.name, COALESCE(p.affiliation, pa.affiliation) AS university
FROM professor_areas pa LEFT JOIN professors p ON p.name = pa.name
ORDER BY pa.name, (p.affiliation = pa.affiliation) DESC, pa.year DESC;

-- Every grant of every linked professor: NSF (id = award id) and other funders
-- (id = '<funder>:<grant id>'), each in its own currency.
CREATE TEMP TABLE x_awards ON COMMIT DROP AS
SELECT DISTINCT i.professor AS name, a.id, a.award_title_text, a.abstract, a.award_amount::numeric AS award_amount,
       NULLIF(a.award_effective_date, '')::date AS starts, NULLIF(a.award_expiry_date, '')::date AS ends,
       'nsf'::text AS funder, 'USD'::text AS currency,
       'https://www.nsf.gov/awardsearch/showAward?AWD_ID=' || a.id AS url
FROM nsf_investigators i
JOIN award_pi_rel r ON r.nsf_id = i.nsf_id
JOIN award a ON a.id = r.award_id
WHERE i.professor IS NOT NULL
UNION
SELECT DISTINCT p.professor, g.funder || ':' || g.grant_id, g.title, g.abstract, g.amount,
       g.starts, g.ends, g.funder, g.currency, g.url
FROM funder_grant_people p JOIN funder_grants g USING (funder, grant_id)
WHERE p.professor IS NOT NULL;

INSERT INTO explorer_faculty (name, university, homepage, scholar_id, areas, area_pubs, recent_pubs,
                              active_awards, total_awards, active_funding, last_award_date, funding)
SELECT f.name, f.university, p.homepage, NULLIF(NULLIF(p.scholar_id, ''), 'NOSCHOLARPAGE'),
       f.areas, f.area_pubs, f.recent_pubs,
       COALESCE(w.active, 0), COALESCE(w.total, 0), COALESCE(w.active_funding, 0), w.last_start, fu.funding
FROM (
  SELECT x.name, a.university, array_agg(x.area ORDER BY x.pubs DESC) AS areas,
         jsonb_object_agg(x.area, round(x.pubs::numeric)) AS area_pubs, sum(x.pubs) AS recent_pubs
  FROM x_pubs x JOIN x_aff a USING (name)
  GROUP BY x.name, a.university
) f
LEFT JOIN professors p ON p.name = f.name
LEFT JOIN (
  SELECT name,
         count(*) FILTER (WHERE ends >= current_date) AS active,
         count(*) AS total,
         -- USD, NSF only; other currencies are in funding
         COALESCE(sum(award_amount) FILTER (WHERE ends >= current_date AND funder = 'nsf'), 0) AS active_funding,
         max(starts) AS last_start
  FROM x_awards GROUP BY name
) w ON w.name = f.name
LEFT JOIN (
  SELECT name, jsonb_agg(jsonb_build_object('funder', funder, 'currency', currency, 'active', active,
                                            'total', total, 'active_amount', active_amount)
                         ORDER BY active DESC, total DESC) AS funding
  FROM (SELECT name, funder, currency,
               count(*) FILTER (WHERE ends >= current_date) AS active, count(*) AS total,
               COALESCE(sum(award_amount) FILTER (WHERE ends >= current_date), 0) AS active_amount
        FROM x_awards GROUP BY name, funder, currency) z
  GROUP BY name
) fu ON fu.name = f.name;

INSERT INTO explorer_work_docs (name, kind, ref, title, year, url, doc)
SELECT x.name, 'award', x.id, x.award_title_text, extract(year FROM x.starts)::int, x.url,
       setweight(to_tsvector('english', COALESCE(x.award_title_text, '')), 'A')
       || setweight(to_tsvector('english', COALESCE(x.abstract, '')), 'B')
FROM x_awards x WHERE x.name IN (SELECT name FROM explorer_faculty)
ON CONFLICT DO NOTHING;

INSERT INTO explorer_work_docs (name, kind, ref, title, year, url, doc)
SELECT p.name, 'paper', p.dblp_key, p.title, p.year, p.url,
       setweight(to_tsvector('english', p.title), 'A')
FROM dblp_papers p WHERE p.name IN (SELECT name FROM explorer_faculty)
ON CONFLICT DO NOTHING;

INSERT INTO explorer_universities (id, name, city, state, country, latitude, longitude, homepage, carnegie,
                                   grad_tuition_in_state, grad_tuition_out_of_state, grad_enrollment,
                                   faculty_count, funded_faculty, area_faculty, area_funded)
SELECT institution_key(u.institution), u.institution, COALESCE(ii.city, u.city), ii.state,
       COALESCE(u.countryabbrv, 'us'), u.latitude, u.longitude, COALESCE(ii.website, u.homepage),
       CASE ii.carnegie_classification WHEN '15' THEN 'R1' WHEN '16' THEN 'R2' END,
       t.grad_tuition_in_state, t.grad_tuition_out_of_state, e.graduate_total,
       fc.faculty, fc.funded, ac.area_faculty, ac.area_funded
FROM (SELECT university, count(*) faculty, count(*) FILTER (WHERE active_awards > 0) funded
      FROM explorer_faculty GROUP BY university) fc
JOIN universities u ON u.institution = fc.university
JOIN (SELECT university, jsonb_object_agg(area, n) area_faculty, jsonb_object_agg(area, nf) area_funded
      FROM (SELECT university, area, count(*) n, count(*) FILTER (WHERE active_awards > 0) nf
            FROM explorer_faculty, unnest(areas) area GROUP BY university, area) z
      GROUP BY university) ac ON ac.university = fc.university
LEFT JOIN ipeds_institutions ii ON ii.unitid = u.ipeds_unitid
LEFT JOIN ipeds_tuition_fees t ON t.unitid = u.ipeds_unitid
LEFT JOIN ipeds_enrollment e ON e.unitid = u.ipeds_unitid
ON CONFLICT (id) DO NOTHING;
`

func buildExplorerTables(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	if _, err := tx.Exec(buildExplorerSQL); err != nil {
		return fmt.Errorf("failed to build explorer tables: %w", err)
	}
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit explorer tables: %w", err)
	}

	var faculty, funded, universities int
	if err := db.QueryRow(`
		SELECT (SELECT count(*) FROM explorer_faculty),
		       (SELECT count(*) FROM explorer_faculty WHERE active_awards > 0),
		       (SELECT count(*) FROM explorer_universities)`).Scan(&faculty, &funded, &universities); err != nil {
		return fmt.Errorf("failed to count explorer rows: %w", err)
	}
	logger.Infof(mainCtx, "🧭 Explorer: %d faculty (%d with an active grant) at %d universities", faculty, funded, universities)
	return nil
}
