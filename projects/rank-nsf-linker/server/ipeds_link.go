package main

import (
	"database/sql"
	"encoding/csv"
	"fmt"
	"os"
	"path/filepath"
	"strconv"

	colly "github.com/gocolly/colly/v2"
)

// Flagships no name rule can pick out ("University of Washington-Seattle Campus" vs
// "-Bothell Campus"). Columns: institution (universities row), unitid, note.
const ipedsLinksFile = "ipeds_links.csv"

func loadCuratedIpedsLinks(tx *sql.Tx) error {
	if _, err := tx.Exec(`CREATE TEMP TABLE ip_curated (institution TEXT, unitid INTEGER) ON COMMIT DROP`); err != nil {
		return fmt.Errorf("failed to create ip_curated: %w", err)
	}
	path := filepath.Join(getRootDirPath(BACKUP_DIR), ipedsLinksFile)
	f, err := os.Open(path)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return fmt.Errorf("failed to open %s: %w", path, err)
	}
	defer f.Close()

	records, err := csv.NewReader(f).ReadAll()
	if err != nil {
		return fmt.Errorf("failed to read %s: %w", path, err)
	}
	for i, rec := range records {
		if i == 0 || len(rec) < 2 {
			continue // header or incomplete row
		}
		unitid, err := strconv.Atoi(rec[1])
		if err != nil {
			return fmt.Errorf("%s row %d: bad unitid %q", path, i+1, rec[1])
		}
		if _, err := tx.Exec(`INSERT INTO ip_curated (institution, unitid) VALUES ($1, $2)`, rec[0], unitid); err != nil {
			return fmt.Errorf("failed to insert curated IPEDS link: %w", err)
		}
	}
	return nil
}

// linkIpedsSQL links US universities rows to IPEDS institutions (universities.ipeds_unitid).
//
// A university is compared under every spelling it is known by (its name and its
// institution_aliases); an IPEDS institution under its name, its IALIAS entries, and its name
// without a "-<X> Campus" suffix or a trailing "-<its city>" / "at <its city>".
// Evidence:
//   - name:   the institution_key of some spelling matches
//   - place:  same city, or same 5-digit ZIP
//   - domain: homepage and IPEDS website share a registrable domain
//
// name + place links; name alone links only when exactly one IPEDS institution has that name;
// a stripped name ("Kent State University") links only when unique, never with place alone —
// some rows carry another campus's address ("University of Nevada" with a Las Vegas ZIP);
// domain needs place too (homepages filled by fuzzy matching are sometimes wrong).
//
// Runs before the merge step. Each IPEDS institution ends up on one row after merging.
// Linked rows are universities (IPEDS lists only postsecondary institutions), take IPEDS's
// website when theirs disagrees, and IPEDS's address and coordinates: geocoding and NSF addresses
// are sometimes another campus's ("University of Nevada" with a Las Vegas ZIP).
const linkIpedsSQL = `
CREATE TEMP TABLE ip_names ON COMMIT DROP AS
SELECT DISTINCT unitid, institution_key(n) AS k, stripped
FROM ipeds_institutions,
     LATERAL (
       SELECT unnest(array_append(regexp_split_to_array(COALESCE(institution_alias, ''), '\s*[|,]\s*'), institution_name)), false
       UNION ALL
       -- flagship campuses: "Purdue University-Main Campus", "University of Washington-Seattle Campus"
       SELECT regexp_replace(institution_name, '\s*-\s*[^-]*campus$|\s+campus\s+immersion$', '', 'i'), true
       UNION ALL
       -- the institution's own city: "Kent State University at Kent", "Indiana University-Bloomington"
       SELECT regexp_replace(institution_name,
         '\s*(-|\mat\M)\s*' || regexp_replace(COALESCE(city, ''), '([.*+?^${}()|\[\]\\])', '\\\1', 'g') || '$', '', 'i'), true
     ) v(n, stripped)
WHERE btrim(n) <> '' AND length(institution_key(n)) > 3;
DELETE FROM ip_names s USING ip_names f WHERE s.stripped AND NOT f.stripped AND s.unitid = f.unitid AND s.k = f.k;
CREATE INDEX ON ip_names (k);

CREATE TEMP TABLE ip_unique ON COMMIT DROP AS
SELECT k FROM ip_names GROUP BY k HAVING count(DISTINCT unitid) = 1;

CREATE TEMP TABLE u_names ON COMMIT DROP AS
SELECT DISTINCT u.institution, institution_key(n) AS k
FROM universities u,
     LATERAL (SELECT u.institution UNION SELECT a.alias FROM institution_aliases a WHERE a.canonical = u.institution) s(n)
WHERE COALESCE(u.countryabbrv, 'us') = 'us';
CREATE INDEX ON u_names (k);

CREATE TEMP TABLE ip_pairs ON COMMIT DROP AS
SELECT un.institution, inn.unitid,
       bool_or(NOT inn.stripped) AS by_name,
       bool_or(NOT inn.stripped AND q.k IS NOT NULL) AS unique_name,
       bool_or(inn.stripped AND q.k IS NOT NULL) AS unique_stripped
FROM u_names un JOIN ip_names inn ON inn.k = un.k LEFT JOIN ip_unique q ON q.k = un.k
GROUP BY un.institution, inn.unitid;

INSERT INTO ip_pairs (institution, unitid, by_name, unique_name, unique_stripped)
SELECT u.institution, i.unitid, false, false, false
FROM (SELECT institution, registrable_domain(homepage) AS d FROM universities
      WHERE COALESCE(countryabbrv, 'us') = 'us') u
JOIN (SELECT unitid, registrable_domain(website) AS d FROM ipeds_institutions) i ON i.d = u.d
WHERE NOT EXISTS (SELECT 1 FROM ip_pairs p WHERE p.institution = u.institution AND p.unitid = i.unitid);

CREATE TEMP TABLE ip_cand ON COMMIT DROP AS
SELECT p.institution, p.unitid, p.by_name, p.unique_name, p.unique_stripped,
       (lower(btrim(u.city)) = lower(btrim(i.city))
        OR (length(regexp_replace(COALESCE(u.zip_code, ''), '\D', '', 'g')) >= 5
            AND left(regexp_replace(COALESCE(u.zip_code, ''), '\D', '', 'g'), 5)
              = left(regexp_replace(COALESCE(i.zip, ''), '\D', '', 'g'), 5))) AS same_place,
       registrable_domain(u.homepage) = registrable_domain(i.website) AS same_domain
FROM ip_pairs p
JOIN universities u ON u.institution = p.institution
JOIN ipeds_institutions i ON i.unitid = p.unitid;

CREATE TEMP TABLE ip_accepted ON COMMIT DROP AS
SELECT institution, unitid, by_name AND COALESCE(same_place, false) AS name_and_place,
       (by_name::int * 2 + unique_stripped::int + COALESCE(same_place, false)::int * 2 + COALESCE(same_domain, false)::int) AS score
FROM ip_cand
WHERE (by_name AND (COALESCE(same_place, false) OR unique_name))
   OR unique_stripped
   OR (COALESCE(same_domain, false) AND COALESCE(same_place, false));

-- Best IPEDS match per row; per IPEDS institution, a representative row. Other rows matched to
-- the same institution by full name + place are the same university under another spelling
-- ("Ucla", "Caltech"): they are recorded as aliases, and the merge step folds them in.
CREATE TEMP TABLE ip_best ON COMMIT DROP AS
SELECT DISTINCT ON (institution) institution, unitid, score, name_and_place
FROM ip_accepted ORDER BY institution, score DESC, unitid;

CREATE TEMP TABLE ip_rep ON COMMIT DROP AS
SELECT DISTINCT ON (b.unitid) b.unitid, b.institution
FROM ip_best b
JOIN universities u ON u.institution = b.institution
LEFT JOIN (SELECT institution, count(*) AS n FROM award GROUP BY institution) n ON n.institution = b.institution
ORDER BY b.unitid, EXISTS (SELECT 1 FROM professor_areas pa WHERE pa.affiliation = u.institution) DESC,
         (u.institution_type = 'university') DESC, b.score DESC, COALESCE(n.n, 0) DESC, u.institution;

CREATE TEMP TABLE ip_same ON COMMIT DROP AS
SELECT b.institution AS alias, r.institution AS canonical, b.unitid
FROM ip_best b JOIN ip_rep r USING (unitid)
WHERE b.institution <> r.institution AND b.name_and_place;

INSERT INTO institution_aliases (alias, canonical, source)
SELECT alias, canonical, 'ipeds' FROM ip_same
ON CONFLICT (alias) DO UPDATE SET canonical = EXCLUDED.canonical, source = 'ipeds'
WHERE institution_aliases.source <> 'curated';

-- Curated links (backup/ipeds_links.csv, loaded into ip_curated) override both rows and IPEDS ids.
CREATE TEMP TABLE ip_final ON COMMIT DROP AS
SELECT unitid, institution FROM (SELECT unitid, institution FROM ip_rep UNION ALL SELECT unitid, alias FROM ip_same) l
WHERE l.unitid NOT IN (SELECT unitid FROM ip_curated) AND l.institution NOT IN (SELECT institution FROM ip_curated)
UNION ALL
SELECT c.unitid, c.institution FROM ip_curated c
WHERE c.institution IN (SELECT institution FROM universities) AND c.unitid IN (SELECT unitid FROM ipeds_institutions);

UPDATE universities SET ipeds_unitid = NULL WHERE ipeds_unitid IS NOT NULL;
UPDATE universities u SET
  ipeds_unitid = l.unitid,
  institution_type = CASE WHEN u.institution_type = 'university_affiliate' THEN u.institution_type
                          ELSE 'university' END,
  homepage  = CASE WHEN i.website IS NOT NULL
                    AND registrable_domain(i.website) IS DISTINCT FROM registrable_domain(u.homepage)
                   THEN i.website ELSE u.homepage END,
  latitude  = COALESCE(i.latitude::real, u.latitude),
  longitude = COALESCE(i.longitude::real, u.longitude),
  street_address = COALESCE(i.address, u.street_address),
  city      = COALESCE(i.city, u.city),
  zip_code  = COALESCE(i.zip, u.zip_code),
  country   = 'United States',
  countryabbrv = 'us',
  region    = 'northamerica'
FROM ip_final l
JOIN ipeds_institutions i ON i.unitid = l.unitid
WHERE u.institution = l.institution;
`

func linkIpedsInstitutions(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	var ipedsRows int
	if err := db.QueryRow(`SELECT count(*) FROM ipeds_institutions`).Scan(&ipedsRows); err != nil {
		return fmt.Errorf("failed to count IPEDS institutions: %w", err)
	}
	if ipedsRows == 0 {
		logger.Warnf(mainCtx, "⚠️ No IPEDS institutions loaded; skipping IPEDS linking.")
		return nil
	}

	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Curated spellings ("Suny At Albany") are evidence here too; the merge step reloads them.
	if _, err := loadCuratedInstitutionAliases(tx); err != nil {
		return err
	}
	if err := loadCuratedIpedsLinks(tx); err != nil {
		return err
	}
	if _, err := tx.Exec(linkIpedsSQL); err != nil {
		return fmt.Errorf("failed to link IPEDS institutions: %w", err)
	}
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit IPEDS links: %w", err)
	}

	var linked, universities int
	if err := db.QueryRow(`
		SELECT count(*) FILTER (WHERE ipeds_unitid IS NOT NULL),
		       count(*) FILTER (WHERE institution_type = 'university' AND COALESCE(countryabbrv, 'us') = 'us')
		FROM universities`).Scan(&linked, &universities); err != nil {
		return fmt.Errorf("failed to count IPEDS links: %w", err)
	}
	logger.Infof(mainCtx, "🏛️  Linked %d rows to IPEDS (%d US rows typed university)", linked, universities)
	return nil
}
