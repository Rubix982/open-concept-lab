package main

import (
	"fmt"

	colly "github.com/gocolly/colly/v2"
)

// linkInvestigatorsSQL decides which NSF investigators are CSRankings faculty.
//
// A candidate pair shares a last name (NSF's last name, or its final word) and a first name
// (or one side's first initial). The name alone is never enough — common names collide — so a
// pair also needs evidence:
//   - same_inst:   one of the investigator's awards is at the professor's CSRankings university
//   - same_domain: the investigator's NSF email domain matches the professor's homepage domain,
//     or the homepage domain of one of the professor's universities
//
// Full first name + either evidence links; first initial needs both. An investigator matching
// more than one professor is linked only if exactly one has both kinds of evidence.
// Links are per NSF person id, so awards from a professor's previous university link too.
const linkInvestigatorsSQL = `
CREATE TEMP TABLE l_inv ON COMMIT DROP AS
SELECT nsf_id, f[1] AS first_tok, l[array_length(l, 1)] AS last_tok, array_to_string(l, '') AS last_full
FROM (SELECT nsf_id, person_name_tokens(first_name) f, person_name_tokens(last_name) l FROM nsf_investigators) x
WHERE array_length(f, 1) >= 1 AND array_length(l, 1) >= 1;

-- CSRankings lists some people under several names ("Dawn Song", "Dawn Xiaodong Song");
-- person_key groups them by scholar id, else homepage. in_areas marks the spelling CSRankings
-- uses in its publication data, which is the one linked.
CREATE TEMP TABLE l_cs ON COMMIT DROP AS
SELECT name, t[1] AS first_tok, t[array_length(t, 1)] AS last_tok, registrable_domain(homepage) AS home_domain,
       COALESCE(NULLIF(NULLIF(scholar_id, ''), 'NOSCHOLARPAGE'), NULLIF(homepage, ''), name) AS person_key,
       name IN (SELECT name FROM professor_areas) AS in_areas
FROM (SELECT name, homepage, scholar_id, person_name_tokens(name) t FROM professors) x
WHERE array_length(t, 1) >= 2;
CREATE INDEX ON l_cs (last_tok);

CREATE TEMP TABLE l_cs_aff ON COMMIT DROP AS
SELECT DISTINCT name, affiliation FROM (
  SELECT name, affiliation FROM professors UNION SELECT name, affiliation FROM professor_areas
) a WHERE affiliation IS NOT NULL;
CREATE INDEX ON l_cs_aff (name, affiliation);

-- Domains that stand for a professor: their homepage's, and their universities' homepages'.
CREATE TEMP TABLE l_cs_domain ON COMMIT DROP AS
SELECT name, home_domain AS domain FROM l_cs WHERE home_domain IS NOT NULL
UNION
SELECT f.name, registrable_domain(u.homepage) FROM l_cs_aff f JOIN universities u ON u.institution = f.affiliation
WHERE registrable_domain(u.homepage) IS NOT NULL;
CREATE INDEX ON l_cs_domain (name, domain);

CREATE TEMP TABLE l_inv_inst ON COMMIT DROP AS
SELECT DISTINCT r.nsf_id, i.inst
FROM award_pi_rel r JOIN award a ON a.id = r.award_id,
     LATERAL (VALUES (a.institution), (a.performing_institution)) i(inst)
WHERE r.nsf_id IS NOT NULL AND i.inst IS NOT NULL;
CREATE INDEX ON l_inv_inst (nsf_id);

CREATE TEMP TABLE l_inv_domain ON COMMIT DROP AS
SELECT DISTINCT nsf_id, registrable_domain(email) AS domain
FROM award_pi_rel WHERE nsf_id IS NOT NULL AND registrable_domain(email) IS NOT NULL;
CREATE INDEX ON l_inv_domain (nsf_id);

CREATE TEMP TABLE l_cand ON COMMIT DROP AS
SELECT i.nsf_id, c.name,
       (c.first_tok = i.first_tok) AS full_first,
       EXISTS (SELECT 1 FROM l_inv_inst ii JOIN l_cs_aff f ON f.affiliation = ii.inst
               WHERE ii.nsf_id = i.nsf_id AND f.name = c.name) AS same_inst,
       EXISTS (SELECT 1 FROM l_inv_domain d JOIN l_cs_domain cd ON cd.domain = d.domain
               WHERE d.nsf_id = i.nsf_id AND cd.name = c.name) AS same_domain,
       c.person_key, c.in_areas
FROM l_inv i
JOIN l_cs c ON c.last_tok IN (i.last_tok, i.last_full)
WHERE c.first_tok = i.first_tok
   OR (length(c.first_tok) = 1 AND c.first_tok = left(i.first_tok, 1))
   OR (length(i.first_tok) = 1 AND i.first_tok = left(c.first_tok, 1));

CREATE TEMP TABLE l_accepted_all ON COMMIT DROP AS
SELECT nsf_id, name, person_key, in_areas, (same_inst AND same_domain) AS both_evidence,
       CASE WHEN same_inst AND same_domain THEN 'name+institution+email'
            WHEN same_inst THEN 'name+institution'
            ELSE 'name+email' END
       || CASE WHEN full_first THEN '' ELSE ' (initial)' END AS method
FROM l_cand
WHERE (full_first AND (same_inst OR same_domain)) OR (same_inst AND same_domain);

-- One row per (investigator, person): the publication-data spelling, strongest evidence first.
CREATE TEMP TABLE l_accepted ON COMMIT DROP AS
SELECT DISTINCT ON (nsf_id, person_key) nsf_id, name, both_evidence, method
FROM l_accepted_all
ORDER BY nsf_id, person_key, in_areas DESC, both_evidence DESC, name;

CREATE TEMP TABLE l_match ON COMMIT DROP AS
SELECT a.nsf_id, a.name, a.method
FROM l_accepted a
JOIN (SELECT nsf_id, count(*) n, count(*) FILTER (WHERE both_evidence) n_both FROM l_accepted GROUP BY nsf_id) g
  ON g.nsf_id = a.nsf_id
WHERE g.n = 1 OR (g.n_both = 1 AND a.both_evidence);

UPDATE nsf_investigators SET professor = NULL, match_method = NULL WHERE professor IS NOT NULL;
UPDATE nsf_investigators i SET professor = m.name, match_method = m.method FROM l_match m WHERE i.nsf_id = m.nsf_id;

UPDATE professors SET nsf_id = NULL WHERE nsf_id IS NOT NULL;
UPDATE professors p SET nsf_id = m.nsf_id
FROM (SELECT DISTINCT ON (name) name, nsf_id FROM l_match ORDER BY name, nsf_id) m
WHERE p.name = m.name;
`

func linkInvestigatorsToProfessors(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	if _, err := tx.Exec(linkInvestigatorsSQL); err != nil {
		return fmt.Errorf("failed to link investigators: %w", err)
	}
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit investigator links: %w", err)
	}

	var investigators, linked, faculty int
	if err := db.QueryRow(`
		SELECT (SELECT count(*) FROM nsf_investigators),
		       (SELECT count(*) FROM nsf_investigators WHERE professor IS NOT NULL),
		       (SELECT count(DISTINCT professor) FROM nsf_investigators)`).Scan(&investigators, &linked, &faculty); err != nil {
		return fmt.Errorf("failed to count links: %w", err)
	}
	logger.Infof(mainCtx, "🧑‍🏫 Linked %d of %d NSF investigators to %d CSRankings faculty", linked, investigators, faculty)
	return nil
}
