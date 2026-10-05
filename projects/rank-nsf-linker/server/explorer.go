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
TRUNCATE explorer_faculty, explorer_universities, explorer_work_docs, professor_variants;

-- One person, several CSRankings names ("Dylan A. Shell" / "Dylan Shell"). Names are one person when
-- they share a Google Scholar id, or a homepage and both first and last name (a department homepage
-- shared by colleagues doesn't merge them). The name with the most publications leads the group.
CREATE TEMP TABLE x_names ON COMMIT DROP AS
SELECT n.name, NULLIF(NULLIF(p.scholar_id, ''), 'NOSCHOLARPAGE') AS sid, NULLIF(p.homepage, '') AS hp,
       t[1] AS first_tok, t[array_length(t, 1)] AS last_tok,
       COALESCE((SELECT sum(pa.count) FROM professor_areas pa WHERE pa.name = n.name), 0) AS pubs
FROM (SELECT name FROM professors UNION SELECT name FROM professor_areas) n
LEFT JOIN (SELECT DISTINCT ON (name) name, scholar_id, homepage FROM professors ORDER BY name) p USING (name)
CROSS JOIN LATERAL (SELECT person_name_tokens(n.name) AS t) tok;

CREATE TEMP TABLE x_groups ON COMMIT DROP AS
WITH g1 AS (
  SELECT name, sid, pubs,
         CASE WHEN hp IS NOT NULL AND first_tok IS NOT NULL THEN 'h:' || hp || '|' || first_tok || '|' || last_tok
              ELSE 'n:' || name END AS k1
  FROM x_names
), g2 AS (
  SELECT name, pubs, COALESCE('s:' || min(sid) OVER (PARTITION BY k1), k1) AS k2 FROM g1
)
SELECT name, g2.pubs, COALESCE('s:' || min(x.sid) OVER (PARTITION BY g2.k2), g2.k2) AS k
FROM g2 JOIN x_names x USING (name);

INSERT INTO professor_variants (name, canonical)
SELECT name, first_value(name) OVER (PARTITION BY k ORDER BY pubs DESC, length(name) DESC, name)
FROM x_groups;

-- Per area, the most papers any of a person's names has (variants can be credited the same papers).
CREATE TEMP TABLE x_pubs ON COMMIT DROP AS
SELECT pv.canonical AS name, z.area, max(z.pubs) AS pubs
FROM (SELECT pa.name, v.area, sum(pa.count) AS pubs
      FROM professor_areas pa JOIN research_area_venues v ON v.venue = pa.area
      WHERE pa.year >= extract(year FROM current_date)::int - 10
      GROUP BY pa.name, v.area) z
JOIN professor_variants pv ON pv.name = z.name
GROUP BY pv.canonical, z.area;

-- A professor's university: CSRankings' current affiliation, else their most recent publication affiliation.
CREATE TEMP TABLE x_aff ON COMMIT DROP AS
SELECT DISTINCT ON (pa.name) pa.name, COALESCE(p.affiliation, pa.affiliation) AS university
FROM professor_areas pa LEFT JOIN professors p ON p.name = pa.name
ORDER BY pa.name, (p.affiliation = pa.affiliation) DESC, pa.year DESC;

-- Every grant of every linked professor: NSF (id = award id) and other funders
-- (id = '<funder>:<grant id>'), each in its own currency.
CREATE TEMP TABLE x_awards ON COMMIT DROP AS
SELECT name, id, award_title_text, abstract, award_amount, starts, ends, funder, currency, url, bool_or(lead) AS lead
FROM (
  SELECT COALESCE(pv.canonical, i.professor) AS name, a.id, a.award_title_text, a.abstract,
         a.award_amount::numeric AS award_amount,
         NULLIF(a.award_effective_date, '')::date AS starts, NULLIF(a.award_expiry_date, '')::date AS ends,
         'nsf'::text AS funder, 'USD'::text AS currency,
         'https://www.nsf.gov/awardsearch/showAward?AWD_ID=' || a.id AS url,
         r.pi_role !~* 'co-' AS lead
  FROM nsf_investigators i
  JOIN award_pi_rel r ON r.nsf_id = i.nsf_id
  JOIN award a ON a.id = r.award_id
  LEFT JOIN professor_variants pv ON pv.name = i.professor
  WHERE i.professor IS NOT NULL
  UNION ALL
  SELECT COALESCE(pv.canonical, p.professor), g.funder || ':' || g.grant_id, g.title, g.abstract, g.amount,
         g.starts, g.ends, g.funder, g.currency, g.url, p.role = 'PI'
  FROM funder_grant_people p JOIN funder_grants g USING (funder, grant_id)
  LEFT JOIN professor_variants pv ON pv.name = p.professor
  WHERE p.professor IS NOT NULL
) z
GROUP BY name, id, award_title_text, abstract, award_amount, starts, ends, funder, currency, url;

-- First top-venue paper (CSRankings), across a person's name spellings: early-career faculty build labs.
CREATE TEMP TABLE x_first ON COMMIT DROP AS
SELECT pv.canonical AS name, min(pa.year) AS first_year
FROM professor_areas pa JOIN professor_variants pv ON pv.name = pa.name
WHERE pa.area !~ '^oas?:'
GROUP BY pv.canonical;

INSERT INTO explorer_faculty (name, university, homepage, scholar_id, areas, area_pubs, recent_pubs,
                              active_awards, total_awards, active_funding, last_award_date, funding, source,
                              first_year, orcid, openalex_id)
SELECT f.name, f.university, p.homepage, NULLIF(NULLIF(p.scholar_id, ''), 'NOSCHOLARPAGE'),
       f.areas, f.area_pubs, f.recent_pubs,
       COALESCE(w.active, 0), COALESCE(w.total, 0), COALESCE(w.active_funding, 0), w.last_start, fu.funding,
       COALESCE(p.source, 'csrankings'), xf.first_year,
       CASE WHEN p.orcid !~ '^0000-0000-0000-' THEN NULLIF(p.orcid, '') END, p.openalex_id
FROM (
  SELECT x.name, a.university, array_agg(x.area ORDER BY x.pubs DESC, x.area) AS areas,
         jsonb_object_agg(x.area, round(x.pubs::numeric)) AS area_pubs, sum(x.pubs) AS recent_pubs
  FROM x_pubs x JOIN x_aff a USING (name)
  GROUP BY x.name, a.university
) f
LEFT JOIN professors p ON p.name = f.name
LEFT JOIN x_first xf ON xf.name = f.name AND COALESCE(p.source, 'csrankings') = 'csrankings'
LEFT JOIN (
  SELECT name,
         count(*) FILTER (WHERE ends >= current_date) AS active,
         count(*) AS total,
         -- USD, NSF grants the person leads; other currencies are in funding
         COALESCE(sum(award_amount) FILTER (WHERE ends >= current_date AND funder = 'nsf' AND lead), 0) AS active_funding,
         max(starts) AS last_start
  FROM x_awards GROUP BY name
) w ON w.name = f.name
LEFT JOIN (
  -- active_amount counts only grants the person leads: a co-investigator's share isn't published, and
  -- the whole amount of a large programme grant would overstate it.
  SELECT name, jsonb_agg(jsonb_build_object('funder', funder, 'currency', currency, 'active', active,
                                            'lead_active', lead_active, 'total', total, 'active_amount', active_amount)
                         ORDER BY active DESC, total DESC) AS funding
  FROM (SELECT name, funder, currency,
               count(*) FILTER (WHERE ends >= current_date) AS active,
               count(*) FILTER (WHERE ends >= current_date AND lead) AS lead_active, count(*) AS total,
               COALESCE(sum(award_amount) FILTER (WHERE ends >= current_date AND lead), 0) AS active_amount
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
SELECT pv.canonical, 'paper', p.dblp_key, p.title, p.year, p.url,
       setweight(to_tsvector('english', p.title), 'A')
FROM dblp_papers p JOIN professor_variants pv ON pv.name = p.name
WHERE pv.canonical IN (SELECT name FROM explorer_faculty)
ON CONFLICT DO NOTHING;

INSERT INTO explorer_universities (id, name, city, state, country, latitude, longitude, homepage, carnegie,
                                   grad_tuition_in_state, grad_tuition_out_of_state, grad_enrollment,
                                   faculty_count, funded_faculty, area_faculty, area_funded)
SELECT institution_key(u.institution), u.institution, COALESCE(ii.city, u.city), ii.state,
       u.countryabbrv, COALESCE(uc.latitude, ii.latitude, u.latitude), COALESCE(uc.longitude, ii.longitude, u.longitude),
       COALESCE(ii.website, u.homepage),
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
LEFT JOIN uc_curated uc ON uc.institution = u.institution
LEFT JOIN ipeds_institutions ii ON ii.unitid = u.ipeds_unitid
LEFT JOIN ipeds_tuition_fees t ON t.unitid = u.ipeds_unitid
LEFT JOIN ipeds_enrollment e ON e.unitid = u.ipeds_unitid
ON CONFLICT (id) DO NOTHING;

-- Each person's newest paper, shown on faculty rows when no goal is searched.
UPDATE explorer_faculty f SET latest_work = l.w
FROM (SELECT DISTINCT ON (name) name, jsonb_build_object('title', title, 'year', year, 'url', url) AS w
      FROM explorer_work_docs WHERE kind = 'paper'
      ORDER BY name, year DESC NULLS LAST, title) l
WHERE l.name = f.name;

-- US: doctoral degrees awarded in the latest IPEDS year (all fields).
UPDATE explorer_universities eu SET doctoral_degrees = c.doctoral_degrees, doctoral_year = c.year
FROM universities u
JOIN (SELECT DISTINCT ON (unitid) unitid, year, doctoral_degrees FROM ipeds_completions
      WHERE doctoral_degrees > 0 ORDER BY unitid, year DESC) c ON c.unitid = u.ipeds_unitid
WHERE eu.name = u.institution;

-- Per funder: how many listed people have its grants, and how many have one running now.
UPDATE explorer_universities eu SET funders = x.funders
FROM (SELECT university, jsonb_agg(jsonb_build_object('funder', funder, 'people', people, 'active_people', active_people)
                                   ORDER BY active_people DESC, people DESC) AS funders
      FROM (SELECT f.university, e->>'funder' AS funder, count(*) AS people,
                   count(*) FILTER (WHERE (e->>'active')::int > 0) AS active_people
            FROM explorer_faculty f, jsonb_array_elements(f.funding) e GROUP BY 1, 2) z
      GROUP BY university) x
WHERE x.university = eu.name;
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

	if err := loadCuratedCoordinates(tx); err != nil {
		return err
	}
	if _, err := tx.Exec(buildExplorerSQL); err != nil {
		return fmt.Errorf("failed to build explorer tables: %w", err)
	}
	if _, err := tx.Exec(buildGrantLandscapeSQL); err != nil {
		return fmt.Errorf("failed to build the grant landscape: %w", err)
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
