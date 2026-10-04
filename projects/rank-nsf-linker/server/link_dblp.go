package main

import (
	"fmt"

	colly "github.com/gocolly/colly/v2"
)

// linkByDblpAffiliationSQL links NSF investigators the main linker left unlinked because they moved:
// CSRankings records today's university, the NSF awards are from an earlier one ("Jiayu Zhou",
// Michigan State → Michigan). DBLP person records list current and former affiliations; an
// investigator links when their full first and last name match a CSRankings professor and one of
// their NSF award institutions is among that professor's DBLP affiliations. Only unlinked
// investigators are considered, and only when exactly one person matches.
const linkByDblpAffiliationSQL = `
CREATE TEMP TABLE d_inv ON COMMIT DROP AS
SELECT nsf_id, f[1] AS first_tok, l[array_length(l, 1)] AS last_tok, array_to_string(l, '') AS last_full
FROM (SELECT nsf_id, person_name_tokens(first_name) f, person_name_tokens(last_name) l
      FROM nsf_investigators WHERE professor IS NULL) x
WHERE array_length(f, 1) >= 1 AND array_length(l, 1) >= 1 AND length(f[1]) > 1;

CREATE TEMP TABLE d_cs ON COMMIT DROP AS
SELECT name, t[1] AS first_tok, t[array_length(t, 1)] AS last_tok,
       CASE WHEN pv.canonical IN (SELECT name FROM professors) THEN pv.canonical ELSE x.name END AS person
FROM (SELECT DISTINCT a.name, person_name_tokens(a.name) t FROM dblp_affiliations a) x
LEFT JOIN professor_variants pv USING (name)
WHERE array_length(t, 1) >= 2 AND length(t[1]) > 1;
CREATE INDEX ON d_cs (last_tok);

-- Each affiliation's comma-separated parts ("Michigan State University", "East Lansing", ...) as keys.
CREATE TEMP TABLE d_aff ON COMMIT DROP AS
SELECT DISTINCT a.name, institution_key(unaccent(trim(part))) AS k
FROM dblp_affiliations a, unnest(string_to_array(a.affiliation, ',')) part
WHERE length(trim(part)) > 3;
CREATE INDEX ON d_aff (name, k);

CREATE TEMP TABLE d_inv_inst ON COMMIT DROP AS
SELECT DISTINCT r.nsf_id, k
FROM award_pi_rel r JOIN award a ON a.id = r.award_id,
     LATERAL (VALUES (a.institution), (a.performing_institution)) i(inst),
     LATERAL (VALUES (institution_key(unaccent(i.inst))),
                     (institution_key(unaccent(institution_parent_name(i.inst))))) kk(k)
WHERE r.nsf_id IN (SELECT nsf_id FROM d_inv) AND i.inst IS NOT NULL AND kk.k <> '';
CREATE INDEX ON d_inv_inst (nsf_id, k);

CREATE TEMP TABLE d_cand ON COMMIT DROP AS
SELECT DISTINCT i.nsf_id, c.person
FROM d_inv i
JOIN d_cs c ON c.last_tok IN (i.last_tok, i.last_full) AND c.first_tok = i.first_tok
WHERE EXISTS (SELECT 1 FROM d_inv_inst ii JOIN d_aff f ON f.k = ii.k
              WHERE ii.nsf_id = i.nsf_id AND f.name = c.name);

UPDATE nsf_investigators n SET professor = c.person, match_method = 'name+dblp-affiliation'
FROM d_cand c
WHERE n.nsf_id = c.nsf_id AND n.professor IS NULL
  AND (SELECT count(*) FROM d_cand c2 WHERE c2.nsf_id = c.nsf_id) = 1;
`

func linkNsfByDblpAffiliation(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}
	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()
	if _, err := tx.Exec(linkByDblpAffiliationSQL); err != nil {
		return fmt.Errorf("failed to link by DBLP affiliation: %w", err)
	}
	if err := tx.Commit(); err != nil {
		return err
	}
	var n int
	_ = db.QueryRow(`SELECT count(*) FROM nsf_investigators WHERE match_method = 'name+dblp-affiliation'`).Scan(&n)
	logger.Infof(mainCtx, "🔗 NSF investigators linked by DBLP affiliation history: %d", n)
	return nil
}
