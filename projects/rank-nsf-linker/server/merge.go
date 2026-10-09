package main

import (
	"database/sql"
	"encoding/csv"
	"fmt"
	"os"
	"path/filepath"

	colly "github.com/gocolly/colly/v2"
)

// Hand-curated spellings that institution_key cannot match on its own
// (abbreviations, typos, departments, campus naming). Columns: alias, canonical, note.
const institutionAliasesFile = "institution_aliases.csv"

// mergeInstitutionsSQL folds every spelling of an institution into one universities row.
// Rows are grouped by, in order of precedence:
//  1. a curated alias (backup/institution_aliases.csv) or an IPEDS alias (two spellings
//     matched by name + place to one IPEDS institution; set by the "Link IPEDS Institutions" step),
//  2. institution_key, when another row shares it (migrations/8_institution_aliases.sql),
//  3. the parent university of an affiliate/department name, when that university exists,
//  4. institution_key otherwise.
//
// Within a group the kept row is the CSRankings spelling when there is one, since faculty
// records use it. All references are repointed before the other rows are deleted, and every
// merged spelling is recorded in institution_aliases.
const mergeInstitutionsSQL = `
CREATE TEMP TABLE m_curated ON COMMIT DROP AS
SELECT institution_key(alias) AS alias_key, canonical, institution_key(canonical) AS canonical_key
FROM institution_aliases WHERE source IN ('curated', 'ipeds');

-- A curated canonical name that no row carries yet becomes a row, built from its best-known variant.
INSERT INTO universities (institution, street_address, city, phone, zip_code, country, region,
                          countryabbrv, homepage, latitude, longitude, institution_type)
SELECT DISTINCT ON (c.canonical) c.canonical, u.street_address, u.city, u.phone, u.zip_code, u.country,
       u.region, u.countryabbrv, u.homepage, u.latitude, u.longitude, 'university'
FROM m_curated c JOIN universities u ON institution_key(u.institution) = c.alias_key
WHERE NOT EXISTS (SELECT 1 FROM universities x WHERE institution_key(x.institution) = c.canonical_key)
ORDER BY c.canonical, (u.latitude IS NULL), u.institution
ON CONFLICT (institution) DO NOTHING;

CREATE TEMP TABLE m_rows ON COMMIT DROP AS
SELECT u.institution,
       u.institution_type,
       institution_key(u.institution) AS own_key,
       institution_key(institution_parent_name(u.institution)) AS parent_key,
       EXISTS (SELECT 1 FROM professor_areas pa WHERE pa.affiliation = u.institution) AS is_cs,
       u.latitude IS NOT NULL AS has_coords,
       COALESCE(n.n_awards, 0) AS n_awards,
       NULL::text AS group_key
FROM universities u
LEFT JOIN (SELECT institution, count(*) AS n_awards FROM award GROUP BY institution) n USING (institution);
CREATE INDEX ON m_rows (own_key);

UPDATE m_rows r SET group_key = COALESCE(
  (SELECT c.canonical_key FROM m_curated c WHERE c.alias_key = r.own_key LIMIT 1),
  CASE WHEN EXISTS (SELECT 1 FROM m_rows o WHERE o.own_key = r.own_key AND o.institution <> r.institution)
       THEN r.own_key END,
  CASE WHEN r.parent_key <> r.own_key AND r.parent_key <> ''
        AND EXISTS (SELECT 1 FROM m_rows p WHERE p.own_key = r.parent_key AND p.institution_type = 'university')
       THEN r.parent_key END,
  r.own_key);

-- A parent that is itself curated into another group takes its affiliates along.
UPDATE m_rows r SET group_key = p.group_key
FROM m_rows p
WHERE r.group_key = p.own_key AND p.group_key <> p.own_key AND r.group_key <> p.group_key;

CREATE TEMP TABLE m_map ON COMMIT DROP AS
SELECT institution AS member,
       first_value(institution) OVER (
         PARTITION BY group_key
         ORDER BY is_cs DESC, (own_key = group_key) DESC, (institution_type = 'university') DESC,
                  has_coords DESC, n_awards DESC, (institution ~ '\mof\M') DESC, institution
       ) AS target
FROM m_rows;
DELETE FROM m_map WHERE member = target;

-- Keep whatever the kept row lacks (coordinates as a pair).
UPDATE universities t SET
  street_address = COALESCE(t.street_address, s.street_address),
  city           = COALESCE(t.city, s.city),
  phone          = COALESCE(t.phone, s.phone),
  zip_code       = COALESCE(t.zip_code, s.zip_code),
  country        = COALESCE(t.country, s.country),
  region         = COALESCE(t.region, s.region),
  countryabbrv   = COALESCE(t.countryabbrv, s.countryabbrv),
  homepage       = COALESCE(NULLIF(t.homepage, ''), s.homepage),
  latitude       = CASE WHEN t.latitude IS NULL THEN s.latitude ELSE t.latitude END,
  longitude      = CASE WHEN t.latitude IS NULL THEN s.longitude ELSE t.longitude END,
  ipeds_unitid   = COALESCE(t.ipeds_unitid, s.ipeds_unitid)
FROM (
  SELECT DISTINCT ON (m.target) m.target, u.*
  FROM m_map m JOIN universities u ON u.institution = m.member
  ORDER BY m.target, (u.latitude IS NULL), (NULLIF(u.homepage, '') IS NULL)
) s
WHERE t.institution = s.target;

UPDATE award a SET institution = m.target FROM m_map m WHERE a.institution = m.member;
UPDATE award a SET performing_institution = m.target FROM m_map m WHERE a.performing_institution = m.member;
UPDATE professors p SET affiliation = m.target FROM m_map m WHERE p.affiliation = m.member;
UPDATE labs l SET institution = m.target FROM m_map m WHERE l.institution = m.member;

-- professor_areas is keyed by (name, affiliation, area, year): fold rather than update.
INSERT INTO professor_areas (name, affiliation, area, count, adjusted_count, year)
SELECT pa.name, m.target, pa.area, max(pa.count), max(pa.adjusted_count), pa.year
FROM professor_areas pa JOIN m_map m ON pa.affiliation = m.member
GROUP BY pa.name, m.target, pa.area, pa.year
ON CONFLICT (name, affiliation, area, year) DO UPDATE SET
  count = GREATEST(professor_areas.count, EXCLUDED.count),
  adjusted_count = GREATEST(professor_areas.adjusted_count, EXCLUDED.adjusted_count);
DELETE FROM professor_areas pa USING m_map m WHERE pa.affiliation = m.member;

INSERT INTO institution_aliases (alias, canonical, source)
SELECT member, target, 'merged' FROM m_map
ON CONFLICT (alias) DO UPDATE SET canonical = EXCLUDED.canonical;
UPDATE institution_aliases a SET canonical = m.target FROM m_map m WHERE a.canonical = m.member;

DELETE FROM universities u USING m_map m WHERE u.institution = m.member;
`

func loadCuratedInstitutionAliases(tx *sql.Tx) (int, error) {
	path := filepath.Join(getRootDirPath(BACKUP_DIR), institutionAliasesFile)
	f, err := os.Open(path)
	if err != nil {
		return 0, fmt.Errorf("failed to open %s: %w", path, err)
	}
	defer f.Close()

	records, err := csv.NewReader(f).ReadAll()
	if err != nil {
		return 0, fmt.Errorf("failed to read %s: %w", path, err)
	}

	if _, err := tx.Exec(`DELETE FROM institution_aliases WHERE source = 'curated'`); err != nil {
		return 0, fmt.Errorf("failed to clear curated aliases: %w", err)
	}

	loaded := 0
	for i, rec := range records {
		if i == 0 || len(rec) < 2 || rec[0] == "" || rec[1] == "" {
			continue // header or incomplete row
		}
		alias, canonical := rec[0], rec[1]
		if _, err := tx.Exec(`
			INSERT INTO institution_aliases (alias, canonical, source) VALUES ($1, $2, 'curated')
			ON CONFLICT (alias) DO UPDATE SET canonical = EXCLUDED.canonical, source = 'curated'`,
			alias, canonical); err != nil {
			return 0, fmt.Errorf("failed to insert alias '%s': %w", alias, err)
		}
		loaded++
	}
	return loaded, nil
}

func mergeDuplicateInstitutions(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	var before int
	if err := db.QueryRow(`SELECT count(*) FROM universities`).Scan(&before); err != nil {
		return fmt.Errorf("failed to count universities: %w", err)
	}

	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	curated, err := loadCuratedInstitutionAliases(tx)
	if err != nil {
		return err
	}
	if _, err := tx.Exec(mergeInstitutionsSQL); err != nil {
		return fmt.Errorf("failed to merge institutions: %w", err)
	}
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit institution merge: %w", err)
	}

	var after int
	if err := db.QueryRow(`SELECT count(*) FROM universities`).Scan(&after); err != nil {
		return fmt.Errorf("failed to count universities: %w", err)
	}
	logger.Infof(mainCtx, "🔗 Loaded %d curated aliases; merged %d institution rows (%d → %d)", curated, before-after, before, after)
	return nil
}
