package main

import (
	"net/http"
	"strings"
)

// explorer_grants: every grant from every funder, whether or not its people are on the map, so a
// search can show where money for a topic goes (by funder, by year, by institution). Built with the
// other explorer tables (buildExplorerTables), after explorer_universities and explorer_faculty.
const buildGrantLandscapeSQL = `
TRUNCATE explorer_grants;

-- One lead per grant: the principal investigator, else the first person listed.
-- "abstract || ''" makes Postgres read the whole value: left() on a compressed value reads only a slice,
-- which can end inside a multi-byte character ("invalid byte sequence for encoding UTF8").
INSERT INTO explorer_grants (funder, id, title, snippet, amount, currency, starts, ends, url, country,
                             lead, institution, profile, programs)
SELECT 'nsf', a.id, a.award_title_text, left(NULLIF(a.abstract, '') || '', 400), a.award_amount, 'USD',
       NULLIF(a.award_effective_date, '')::date, NULLIF(a.award_expiry_date, '')::date,
       'https://www.nsf.gov/awardsearch/showAward?AWD_ID=' || a.id, 'us',
       pi.full_name, NULLIF(a.institution, ''), pi.profile, pe.programs
FROM award a
LEFT JOIN (SELECT award_id, array_agg(DISTINCT name) AS programs FROM program_element
           WHERE COALESCE(name, '') <> '' GROUP BY award_id) pe ON pe.award_id = a.id
LEFT JOIN (
  SELECT DISTINCT ON (r.award_id) r.award_id, i.full_name, f.name AS profile
  FROM award_pi_rel r
  JOIN nsf_investigators i ON i.nsf_id = r.nsf_id
  LEFT JOIN professor_variants pv ON pv.name = i.professor
  LEFT JOIN explorer_faculty f ON f.name = COALESCE(pv.canonical, i.professor)
  ORDER BY r.award_id, r.pi_role ~* 'co-', f.name IS NULL
) pi ON pi.award_id = a.id
WHERE COALESCE(a.award_title_text, '') <> '';

INSERT INTO explorer_grants (funder, id, title, snippet, amount, currency, starts, ends, url, country,
                             lead, institution, profile, scheme)
SELECT g.funder, g.grant_id, g.title, left(NULLIF(g.abstract, '') || '', 400), g.amount, g.currency, g.starts, g.ends,
       g.url, g.country, p.full_name, p.institution, p.profile, NULLIF(g.scheme, '')
FROM funder_grants g
LEFT JOIN (
  SELECT DISTINCT ON (fp.funder, fp.grant_id) fp.funder, fp.grant_id, fp.full_name,
         NULLIF(fp.institution, '') AS institution, f.name AS profile
  FROM funder_grant_people fp
  LEFT JOIN professor_variants pv ON pv.name = fp.professor
  LEFT JOIN explorer_faculty f ON f.name = COALESCE(pv.canonical, fp.professor)
  ORDER BY fp.funder, fp.grant_id, fp.role <> 'PI', NULLIF(fp.institution, '') IS NULL
) p ON p.funder = g.funder AND p.grant_id = g.grant_id
WHERE COALESCE(g.title, '') <> ''
ON CONFLICT DO NOTHING;

-- Institutions on the map: a key per university name and alias; keys shared by two universities dropped.
CREATE TEMP TABLE xg_uni ON COMMIT DROP AS
SELECT k, min(id) AS id FROM (
  SELECT institution_key(name) AS k, id FROM explorer_universities
  UNION ALL
  SELECT institution_key(a.alias), eu.id FROM institution_aliases a JOIN explorer_universities eu ON eu.name = a.canonical
) x WHERE k <> '' GROUP BY k HAVING count(DISTINCT id) = 1;

-- A grant's institution matches by its whole name, each " | " part (French labs list their
-- university), a part's parent university, or the accent-free spelling; the earliest part wins.
CREATE TEMP TABLE xg_keys ON COMMIT DROP AS
SELECT g.institution, part.ord, k.k
FROM (SELECT DISTINCT institution FROM explorer_grants WHERE institution IS NOT NULL) g
CROSS JOIN LATERAL unnest(array_prepend(g.institution, string_to_array(g.institution, ' | '))) WITH ORDINALITY part(name, ord)
CROSS JOIN LATERAL unnest(ARRAY[institution_key(part.name), institution_key(institution_parent_name(part.name)),
                                institution_key(unaccent(part.name))]) k(k);

CREATE TEMP TABLE xg_inst ON COMMIT DROP AS
SELECT DISTINCT ON (x.institution) x.institution, u.id
FROM xg_keys x JOIN xg_uni u ON u.k = x.k
ORDER BY x.institution, x.ord;
CREATE INDEX ON xg_inst (institution);

UPDATE explorer_grants g SET university_id = i.id FROM xg_inst i WHERE i.institution = g.institution;

-- A person on the map holds the grant at their university even when the funder's spelling didn't match.
UPDATE explorer_grants g SET university_id = u.id
FROM explorer_faculty f JOIN explorer_universities u ON u.name = f.university
WHERE g.university_id IS NULL AND g.profile = f.name;

-- Signals (NSF programme reference 1045 is CAREER). training: pays PhD students (NIH institutional training grants, NSF Research Traineeships).
-- new_lab: a PI starting out, with money (NSF CAREER, ERC Starting, ARC DECRA, NIH R00 = the faculty
-- phase of K99/R00, KAKEN early-career and young-scientist grants, SNSF Ambizione/Eccellenza/PRIMA,
-- ANR JCJC, UKRI new-investigator awards).
UPDATE explorer_grants SET signal = 'training'
WHERE (funder = 'nih' AND scheme IN ('T32', 'TL1', 'T90'))
   OR (funder = 'nsf' AND programs && ARRAY['NSF Research Traineeship (NRT)']);
UPDATE explorer_grants SET signal = 'new_lab'
WHERE signal IS NULL AND (
      (funder = 'nsf' AND (title ILIKE 'CAREER:%' OR programs && ARRAY['CAREER: FACULTY EARLY CAR DEV']
                           OR id IN (SELECT award_id FROM program_reference WHERE code = '1045')))
   OR (funder = 'erc' AND scheme = 'ERC-STG')
   OR (funder = 'arc' AND scheme = 'Discovery Early Career Researcher Award')
   OR (funder = 'nih' AND scheme = 'R00')
   OR (funder = 'kaken' AND (scheme ILIKE '%Early-Career%' OR scheme ILIKE '%Young Scientists%'))
   OR (funder = 'snsf' AND scheme ~* 'ambizione|eccellenza|prima')
   OR (funder = 'anr' AND scheme IN ('JCJC', 'JC'))
   OR (funder = 'ukri' AND scheme ILIKE '%new investigator%'));

UPDATE explorer_faculty f SET new_lab = x.grant
FROM (SELECT DISTINCT ON (profile) profile,
             jsonb_build_object('funder', funder, 'scheme', scheme, 'title', title, 'url', url,
                                'starts', starts, 'ends', ends) AS grant
      FROM explorer_grants
      WHERE signal = 'new_lab' AND ends >= current_date AND profile IS NOT NULL
      ORDER BY profile, starts DESC) x
WHERE x.profile = f.name;

UPDATE explorer_universities u SET training = x.grants
FROM (SELECT university_id, jsonb_agg(jsonb_build_object('funder', funder, 'title', title, 'url', url,
                                                         'lead', lead, 'profile', profile, 'ends', ends)
                                      ORDER BY ends DESC) AS grants
      FROM explorer_grants
      WHERE signal = 'training' AND ends >= current_date AND university_id IS NOT NULL
      GROUP BY university_id) x
WHERE x.university_id = u.id;

UPDATE explorer_grants SET doc =
  setweight(to_tsvector('english', title), 'A') ||
  setweight(to_tsvector('english', COALESCE(snippet, '')), 'B');
`

type landscapeFunder struct {
	Funder   string   `json:"funder"`
	Currency *string  `json:"currency"`
	Grants   int      `json:"grants"`
	Active   int      `json:"active"`
	Amount   *float64 `json:"amount"`        // all matching grants with an amount, in Currency
	ActiveAm *float64 `json:"active_amount"` // the active ones
}

type landscapeYear struct {
	Year   int    `json:"year"`
	Funder string `json:"funder"`
	Grants int    `json:"grants"`
}

type landscapePlace struct {
	Institution  string  `json:"institution"`
	UniversityID *string `json:"university_id"`
	Country      *string `json:"country"`
	Grants       int     `json:"grants"`
	Active       int     `json:"active"`
	People       int     `json:"people"` // leads who are in Advisor Atlas
}

type landscapeGrant struct {
	Funder       string   `json:"funder"`
	ID           string   `json:"id"`
	Title        string   `json:"title"`
	Snippet      *string  `json:"snippet"`
	Amount       *float64 `json:"amount"`
	Currency     *string  `json:"currency"`
	Starts       *string  `json:"starts"`
	Ends         *string  `json:"ends"`
	URL          *string  `json:"url"`
	Lead         *string  `json:"lead"`
	Institution  *string  `json:"institution"`
	UniversityID *string  `json:"university_id"`
	Profile      *string  `json:"profile"`
}

// getExplorerLandscape: where money for a search goes, across every grant loaded (linked to someone on
// the map or not): totals by funder, grants started per year, the institutions receiving them, and the
// best-matching grants. Keyword match on title and the start of the abstract.
// Params: q (required), active=1 (running grants only), country.
func getExplorerLandscape(w http.ResponseWriter, r *http.Request) {
	db, err := GetDB()
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "database unavailable", err)
		return
	}
	v := r.URL.Query()
	q := strings.TrimSpace(v.Get("q"))
	if q == "" {
		writeJSON(w, http.StatusOK, map[string]any{"total": 0})
		return
	}
	active := v.Get("active") == "1"
	country := strings.ToLower(strings.TrimSpace(v.Get("country")))

	tx, err := db.Begin()
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "database unavailable", err)
		return
	}
	defer tx.Rollback()
	if _, err := tx.Exec(`
		CREATE TEMP TABLE m ON COMMIT DROP AS
		SELECT g.*, ts_rank_cd(g.doc, q, 1) AS rank, g.ends >= current_date AS running
		FROM explorer_grants g, websearch_to_tsquery('english', $1) q
		WHERE g.doc @@ q AND (NOT $2 OR g.ends >= current_date) AND ($3 = '' OR g.country = $3)`,
		q, active, country); err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to search grants", err)
		return
	}

	out := map[string]any{}
	var total, running int
	if err := tx.QueryRow(`SELECT count(*), count(*) FILTER (WHERE running) FROM m`).Scan(&total, &running); err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to count grants", err)
		return
	}
	out["total"], out["active"] = total, running

	funders := []landscapeFunder{}
	rows, err := tx.Query(`
		SELECT funder, max(currency), count(*), count(*) FILTER (WHERE running),
		       sum(amount), sum(amount) FILTER (WHERE running)
		FROM m GROUP BY funder ORDER BY count(*) DESC`)
	if err == nil {
		for rows.Next() {
			var f landscapeFunder
			if rows.Scan(&f.Funder, &f.Currency, &f.Grants, &f.Active, &f.Amount, &f.ActiveAm) == nil {
				funders = append(funders, f)
			}
		}
		rows.Close()
	}
	out["funders"] = funders

	years := []landscapeYear{}
	rows, err = tx.Query(`
		SELECT extract(year FROM starts)::int AS y, funder, count(*) FROM m
		WHERE starts IS NOT NULL AND starts >= make_date(extract(year FROM current_date)::int - 15, 1, 1)
		GROUP BY y, funder ORDER BY y, funder`)
	if err == nil {
		for rows.Next() {
			var y landscapeYear
			if rows.Scan(&y.Year, &y.Funder, &y.Grants) == nil {
				years = append(years, y)
			}
		}
		rows.Close()
	}
	out["years"] = years

	places := []landscapePlace{}
	rows, err = tx.Query(`
		SELECT COALESCE(u.name, m.institution), m.university_id, COALESCE(u.country, min(m.country)), count(*),
		       count(*) FILTER (WHERE running), count(DISTINCT profile)
		FROM m LEFT JOIN explorer_universities u ON u.id = m.university_id
		WHERE m.institution IS NOT NULL
		GROUP BY COALESCE(u.name, m.institution), m.university_id, u.country
		ORDER BY count(*) FILTER (WHERE running) DESC, count(*) DESC LIMIT 25`)
	if err == nil {
		for rows.Next() {
			var p landscapePlace
			if rows.Scan(&p.Institution, &p.UniversityID, &p.Country, &p.Grants, &p.Active, &p.People) == nil {
				places = append(places, p)
			}
		}
		rows.Close()
	}
	out["places"] = places

	// NSF programmes funding these grants: names a student can look up for calls and deadlines.
	type program struct {
		Name    string `json:"name"`
		Grants  int    `json:"grants"`
		Running int    `json:"running"`
	}
	programs := []program{}
	rows, err = tx.Query(`
		SELECT p, count(*), count(*) FILTER (WHERE running) FROM m, unnest(m.programs) p
		GROUP BY p ORDER BY count(*) FILTER (WHERE running) DESC, count(*) DESC LIMIT 8`)
	if err == nil {
		for rows.Next() {
			var p program
			if rows.Scan(&p.Name, &p.Grants, &p.Running) == nil {
				programs = append(programs, p)
			}
		}
		rows.Close()
	}
	out["programs"] = programs

	grants := []landscapeGrant{}
	rows, err = tx.Query(`
		SELECT funder, id, title, snippet, amount, currency, starts::text, ends::text, url, lead, institution,
		       university_id, profile
		FROM m
		ORDER BY rank * exp(-greatest(extract(year FROM current_date) - COALESCE(extract(year FROM starts), 2010), 0) / 8.0) DESC
		LIMIT 40`)
	if err == nil {
		for rows.Next() {
			var g landscapeGrant
			if rows.Scan(&g.Funder, &g.ID, &g.Title, &g.Snippet, &g.Amount, &g.Currency, &g.Starts, &g.Ends, &g.URL,
				&g.Lead, &g.Institution, &g.UniversityID, &g.Profile) == nil {
				grants = append(grants, g)
			}
		}
		rows.Close()
	}
	out["grants"] = grants
	writeJSON(w, http.StatusOK, out)
}
