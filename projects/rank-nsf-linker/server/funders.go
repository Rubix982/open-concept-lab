package main

import (
	"database/sql"
	"encoding/csv"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"

	colly "github.com/gocolly/colly/v2"
	"github.com/lib/pq"
)

// Grants from funders other than NSF. Each funder has a normaliser in server/scripts/grants/
// that writes data/grants/<funder>_grants.csv and <funder>_people.csv in one common format;
// the pipeline loads whatever is there, so a funder is added by running its script.

// grantFundersByCountry lists, per university country, the funders whose grants are loaded
// for it: the explorer only speaks about grants where it has the data. NSF is always there; the
// others come from funder_grants.country (the host institution's country), cached briefly.
var fundersCache struct {
	sync.Mutex
	at        time.Time
	byCountry map[string][]string
}

func grantFundersByCountry(db *sql.DB) map[string][]string {
	fundersCache.Lock()
	defer fundersCache.Unlock()
	if fundersCache.byCountry != nil && time.Since(fundersCache.at) < time.Hour { // cleared on rebuild
		return fundersCache.byCountry
	}
	m := map[string][]string{"us": {"nsf"}}
	// A funder counts for a country with at least 2 grants there: the one ERC grant hosted in the
	// US made "no NSF or ERC or NIH grant" the sentence for US faculty.
	rows, err := db.Query(`SELECT lower(country), funder FROM funder_grants
		WHERE country IS NOT NULL AND country <> '' GROUP BY 1, 2 HAVING count(*) >= 2 ORDER BY 1, 2`)
	if err == nil {
		defer rows.Close()
		for rows.Next() {
			var country, funder string
			if rows.Scan(&country, &funder) == nil {
				m[country] = append(m[country], funder)
			}
		}
	}
	fundersCache.at, fundersCache.byCountry = time.Now(), m
	return m
}

// funderNames are the names students see.
var funderNames = map[string]string{
	"nsf":     "NSF",
	"marsden": "Marsden Fund",
	"arc":     "Australian Research Council",
	"ukri":    "UKRI",
	"anr":     "ANR",
	"erc":     "ERC",
	"snsf":    "SNSF",
	"kaken":   "KAKEN",
	"nih":     "NIH",
	"rgc":     "RGC",
	"nserc":   "NSERC",
	"nwo":     "NWO",
	"fwf":     "FWF (Austria)",
	// via OpenAlex awards (scripts/grants/openalex_awards.py)
	"nsfc":     "NSFC (China)",
	"nstc":     "NSTC (Taiwan)",
	"cihr":     "CIHR (Canada)",
	"sshrc":    "SSHRC (Canada)",
	"fapesp":   "FAPESP (Brazil)",
	"fct":      "FCT (Portugal)",
	"anid":     "ANID (Chile)",
	"rcn":      "Research Council of Norway",
	"nhmrc":    "NHMRC (Australia)",
	"tubitak":  "TÜBİTAK (Turkey)",
	"vr":       "Swedish Research Council",
	"vinnova":  "Vinnova (Sweden)",
	"formas":   "Formas (Sweden)",
	"forte":    "Forte (Sweden)",
	"ncn":      "NCN (Poland)",
	"fwo":      "FWO (Flanders, Belgium)",
	"isf":      "Israel Science Foundation",
	"sfi":      "Research Ireland (SFI)",
	"wellcome": "Wellcome",
	"amed":     "AMED (Japan)",
	"zonmw":    "ZonMw (Netherlands)",
	"dff":      "Independent Research Fund Denmark",
	"isciii":   "ISCIII (Spain)",
	"nafosted": "NAFOSTED (Vietnam)",
	"icmr":     "ICMR (India)",
	"nsf-lk":   "NSF Sri Lanka",
	"hec":      "HEC NRPU (Pakistan)",
}

// getExplorerFunders: GET /explorer/funders — funder names and the countries each one covers.
func getExplorerFunders(w http.ResponseWriter, r *http.Request) {
	db, err := GetDB()
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "database unavailable", err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"names": funderNames, "by_country": grantFundersByCountry(db)})
}

const grantsDataDir = "grants"

var grantColumns = []string{"funder", "grant_id", "title", "abstract", "amount", "currency", "starts", "ends",
	"url", "country", "scheme", "field"}
var peopleColumns = []string{"funder", "grant_id", "full_name", "first_name", "last_name", "role", "institution", "orcid"}

// loadFunderGrants replaces funder_grants / funder_grant_people with the normalised CSVs.
func loadFunderGrants(mainCtx *colly.Context) error {
	dir := filepath.Join(getRootDirPath(DATA_DIR), grantsDataDir)
	grantFiles, _ := filepath.Glob(filepath.Join(dir, "*_grants.csv"))
	sort.Strings(grantFiles)
	if len(grantFiles) == 0 {
		logger.Warnf(mainCtx, "⚠️ No normalised grant files in %s; skipping (see server/scripts/grants/)", dir)
		return nil
	}

	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}
	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Staging tables are all text and unconstrained: CSVs may repeat a key, and the insert
	// below converts types and keeps one row per key.
	if _, err := tx.Exec(`
		TRUNCATE funder_grants, funder_grant_people;
		CREATE TEMP TABLE fg_stage (funder text, grant_id text, title text, abstract text, amount text,
		  currency text, starts text, ends text, url text, country text, scheme text, field text) ON COMMIT DROP;
		CREATE TEMP TABLE fp_stage (funder text, grant_id text, full_name text, first_name text, last_name text,
		  role text, institution text, orcid text) ON COMMIT DROP;`); err != nil {
		return fmt.Errorf("failed to prepare funder grant staging: %w", err)
	}

	for _, gf := range grantFiles {
		pf := strings.TrimSuffix(gf, "_grants.csv") + "_people.csv"
		g, err := copyCSVInto(tx, gf, "fg_stage", grantColumns)
		if err != nil {
			return err
		}
		p, err := copyCSVInto(tx, pf, "fp_stage", peopleColumns)
		if err != nil {
			return err
		}
		logger.Infof(mainCtx, "💷 %s: %d grants, %d investigators", filepath.Base(gf), g, p)
	}

	if _, err := tx.Exec(`
		INSERT INTO funder_grants
		SELECT DISTINCT ON (funder, grant_id) funder, grant_id, html_unescape(title), NULLIF(html_unescape(abstract), ''),
		       NULLIF(amount, '')::numeric, NULLIF(currency, ''),
		       NULLIF(starts, '')::date, NULLIF(ends, '')::date, NULLIF(url, ''), lower(NULLIF(country, '')),
		       NULLIF(scheme, ''), NULLIF(field, '')
		FROM fg_stage WHERE COALESCE(title, '') <> ''
		ORDER BY funder, grant_id;

		INSERT INTO funder_grant_people (funder, grant_id, full_name, first_name, last_name, role, institution, orcid)
		SELECT DISTINCT ON (funder, grant_id, full_name) funder, grant_id, full_name, NULLIF(first_name, ''),
		       NULLIF(last_name, ''), NULLIF(role, ''), NULLIF(institution, ''), NULLIF(orcid, '')
		FROM fp_stage
		WHERE COALESCE(full_name, '') <> '' AND (funder, grant_id) IN (SELECT funder, grant_id FROM funder_grants)
		ORDER BY funder, grant_id, full_name, (role = 'PI') DESC;`); err != nil {
		return fmt.Errorf("failed to load funder grants: %w", err)
	}
	return tx.Commit()
}

// copyCSVInto streams a common-format CSV into a staging table, checking its header.
func copyCSVInto(tx *sql.Tx, path, table string, columns []string) (int, error) {
	f, err := os.Open(path)
	if err != nil {
		return 0, fmt.Errorf("failed to open %s: %w", path, err)
	}
	defer f.Close()

	r := csv.NewReader(f)
	header, err := r.Read()
	if err != nil {
		return 0, fmt.Errorf("failed to read %s: %w", path, err)
	}
	if strings.Join(header, ",") != strings.Join(columns, ",") {
		return 0, fmt.Errorf("%s: header %v, want %v", path, header, columns)
	}

	stmt, err := tx.Prepare(pq.CopyIn(table, columns...))
	if err != nil {
		return 0, fmt.Errorf("failed to start COPY into %s: %w", table, err)
	}
	n := 0
	for {
		rec, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			stmt.Close()
			return 0, fmt.Errorf("%s row %d: %w", path, n+2, err)
		}
		vals := make([]any, len(rec))
		for i, v := range rec {
			vals[i] = strings.ToValidUTF8(v, "")
		}
		if _, err := stmt.Exec(vals...); err != nil {
			stmt.Close()
			return 0, fmt.Errorf("%s row %d: %w", path, n+2, err)
		}
		n++
	}
	if _, err := stmt.Exec(); err != nil {
		stmt.Close()
		return 0, fmt.Errorf("failed to flush COPY into %s: %w", table, err)
	}
	return n, stmt.Close()
}

// linkFunderGrantsSQL matches funder-grant investigators to CSRankings faculty: same last name,
// same first name or initial (many funders list initials only: "HD Cooper-Thomas"), and the
// investigator's institution is one of the professor's universities — by matching key, by a
// known alias, or by its parent university. Without the institution the name alone never links.
// An investigator matching more than one CSRankings person is left unlinked, and initials with a
// very common surname count only on computing-field grants.
const linkFunderGrantsSQL = `
UPDATE funder_grant_people SET professor = NULL, match_method = NULL WHERE professor IS NOT NULL;

CREATE TEMP TABLE fl_people ON COMMIT DROP AS
SELECT funder, grant_id, full_name, institution,
       (first_name ~ '^([A-Z]\.?\s*){1,4}$') AS first_is_initials,
       CASE WHEN first_name ~ '^([A-Z]\.?\s*){1,4}$' THEN lower(left(first_name, 1))
            ELSE (person_name_tokens(first_name))[1] END AS first_tok,
       l[array_length(l, 1)] AS last_tok, array_to_string(l, '') AS last_full
FROM (SELECT *, person_name_tokens(COALESCE(last_name, full_name)) l FROM funder_grant_people) x
WHERE array_length(l, 1) >= 1 AND COALESCE(first_name, '') <> '';

-- Every key an institution can match: each name it lists (a French lab lists its parent university,
-- CNRS, Inria, ... as "LIP6 | Sorbonne Université | CNRS"), each name's parent university, and its
-- alias's canonical name.
CREATE TEMP TABLE fl_inst ON COMMIT DROP AS
WITH n AS (
  SELECT DISTINCT institution, trim(name) AS name
  FROM fl_people, unnest(string_to_array(institution, ' | ')) name
  WHERE institution IS NOT NULL
)
SELECT DISTINCT institution, k FROM (
  SELECT institution, institution_key(name) k FROM n
  UNION ALL
  SELECT institution, institution_key(institution_parent_name(name)) FROM n
  UNION ALL
  -- institution_key drops accented letters; compare the transliterated name too ("École" = "Ecole")
  SELECT institution, institution_key(unaccent(name)) FROM n
  UNION ALL
  SELECT n.institution, institution_key(a.canonical) FROM n
  JOIN institution_aliases a ON institution_key(a.alias) = institution_key(n.name)
) x WHERE k <> '';
CREATE INDEX ON fl_inst (institution);

CREATE TEMP TABLE fl_cs ON COMMIT DROP AS
SELECT name, t[1] AS first_tok, t[array_length(t, 1)] AS last_tok,
       COALESCE(NULLIF(NULLIF(scholar_id, ''), 'NOSCHOLARPAGE'), NULLIF(homepage, ''), name) AS person_key,
       name IN (SELECT name FROM professor_areas) AS in_areas
FROM (SELECT name, homepage, scholar_id, person_name_tokens(name) t FROM professors) x
WHERE array_length(t, 1) >= 2;
CREATE INDEX ON fl_cs (last_tok);

CREATE TEMP TABLE fl_cs_inst ON COMMIT DROP AS
WITH a AS (
  SELECT name, affiliation FROM professors WHERE affiliation IS NOT NULL
  UNION SELECT name, affiliation FROM professor_areas WHERE affiliation IS NOT NULL
)
SELECT DISTINCT name, k FROM (
  SELECT name, institution_key(affiliation) AS k FROM a
  UNION SELECT name, institution_key(unaccent(affiliation)) FROM a
) x;
CREATE INDEX ON fl_cs_inst (name, k);

CREATE TEMP TABLE fl_cand ON COMMIT DROP AS
SELECT p.funder, p.grant_id, p.full_name, c.name, c.person_key, c.in_areas,
       (c.first_tok = p.first_tok AND NOT p.first_is_initials AND length(c.first_tok) > 1) AS full_first
FROM fl_people p
JOIN fl_cs c ON c.last_tok IN (p.last_tok, p.last_full)
WHERE (c.first_tok = p.first_tok
       OR (length(p.first_tok) = 1 AND p.first_tok = left(c.first_tok, 1))
       OR (length(c.first_tok) = 1 AND c.first_tok = left(p.first_tok, 1)))
  AND EXISTS (SELECT 1 FROM fl_inst i JOIN fl_cs_inst ci ON ci.k = i.k
              WHERE i.institution = p.institution AND ci.name = c.name);

-- Initials are weak evidence for very common surnames ("JL Zhang" at a large university):
-- there, an initial-only match also needs the grant to be in a computing field.
DELETE FROM fl_cand c
USING fl_people p, funder_grants g
WHERE NOT c.full_first
  AND p.funder = c.funder AND p.grant_id = c.grant_id AND p.full_name = c.full_name
  AND g.funder = c.funder AND g.grant_id = c.grant_id
  AND p.last_tok IN ('zhang','wang','li','liu','chen','yang','huang','zhao','wu','zhou','xu','sun','ma','zhu',
                     'hu','guo','he','lin','gao','luo','zheng','liang','xie','song','tang','han','feng','deng',
                     'cao','peng','zeng','xiao','tian','dong','pan','yuan','cai','jiang','yu','du','ye','cheng',
                     'kim','lee','park','choi','jung','kang','cho','yoon','jang','lim','nguyen','tran','le','pham',
                     'singh','kumar','sharma','gupta','patel','khan','ali','ahmed','smith','jones','brown','wilson')
  AND COALESCE(g.field, '') !~* '^(MIS|46|08)|comput|informat';

-- One row per (investigator, person): CSRankings' publication-data spelling first.
CREATE TEMP TABLE fl_best ON COMMIT DROP AS
SELECT DISTINCT ON (funder, grant_id, full_name, person_key) *
FROM fl_cand ORDER BY funder, grant_id, full_name, person_key, in_areas DESC, full_first DESC, name;

UPDATE funder_grant_people p
SET professor = b.name,
    match_method = CASE WHEN b.full_first THEN 'name+institution' ELSE 'initial+institution' END
FROM fl_best b
WHERE p.funder = b.funder AND p.grant_id = b.grant_id AND p.full_name = b.full_name
  AND (SELECT count(*) FROM fl_best o
       WHERE o.funder = b.funder AND o.grant_id = b.grant_id AND o.full_name = b.full_name) = 1;
`

func linkFunderGrants(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}
	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()
	if _, err := tx.Exec(linkFunderGrantsSQL); err != nil {
		return fmt.Errorf("failed to link funder grants: %w", err)
	}
	if err := tx.Commit(); err != nil {
		return err
	}

	rows, err := db.Query(`
		SELECT funder, count(*), count(professor), count(DISTINCT professor)
		FROM funder_grant_people GROUP BY funder ORDER BY funder`)
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var funder string
		var people, linked, profs int
		if err := rows.Scan(&funder, &people, &linked, &profs); err != nil {
			return err
		}
		logger.Infof(mainCtx, "🔗 %s: linked %d of %d investigators to %d faculty and researchers", funder, linked, people, profs)
	}
	return rows.Err()
}
