package main

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"

	colly "github.com/gocolly/colly/v2"
)

// Researchers outside computer science, from OpenAlex (server/scripts/openalex/fields.py writes
// data/openalex/fields_people.csv and fields_works.csv). They are added to professors (source
// 'openalex') and professor_areas (venue 'oa:<field id>', see migration 17), so linking, the
// explorer and the semantic index treat them like CSRankings faculty. A name CSRankings already
// lists is skipped: same-name people can't be told apart here.

// openAlexMaxWorksPerPerson caps each OpenAlex researcher's papers (fewer than DBLP's 30: there are
// many more of them, and each paper is a vector in the semantic index).
const openAlexMaxWorksPerPerson = 10

// notAPaper matches OpenAlex "works" that are front matter or data deposits, not papers: they
// crowded out real papers in search ("Data for EMSL Project 50414 from April 2021" topped
// "robot learning"). The cached responses don't carry OpenAlex's work type, so titles decide.
const notAPaper = `^\s*(contributors|list of contributors|introduction|preface|foreword|editorial|erratum|corrigendum|` +
	`references|index|front matter|back matter|contents|table of contents|acknowledg(e)?ments|author index|` +
	`title page|cover|copyright)\s*\.?\s*$` +
	`|^data for |^dataset\y|subset for:|^supplementary (data|material|information)|^(erratum|correction|retraction)( to|:)`

var (
	fieldsPeopleColumns = []string{"openalex_id", "name", "university", "area", "orcid", "works", "cited_by", "h_index", "subfields"}
	subfieldColumns     = []string{"subfield_id", "name", "field_id"}
	fieldsWorksColumns  = []string{"openalex_id", "work_id", "title", "year", "venue", "doi", "abstract"}
)

func openAlexFieldsPath(name string) string {
	return filepath.Join(getRootDirPath(DATA_DIR), "openalex", name)
}

// loadOpenAlexResearchers runs after "Sync Professor Interests" (which reloads professor_areas).
func loadOpenAlexResearchers(mainCtx *colly.Context) error {
	people := openAlexFieldsPath("fields_people.csv")
	if _, err := os.Stat(people); err != nil {
		logger.Warnf(mainCtx, "⚠️ %s not found; skipping (see server/scripts/openalex/fields.py)", people)
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

	if _, err := tx.Exec(`
		DELETE FROM professor_areas WHERE area LIKE 'oa:%' OR area LIKE 'oas:%';
		DELETE FROM professors WHERE source = 'openalex';
		CREATE TEMP TABLE oa_people (openalex_id text, name text, university text, area text, orcid text,
		  works text, cited_by text, h_index text, subfields text) ON COMMIT DROP;
		CREATE TEMP TABLE oa_works (openalex_id text, work_id text, title text, year text, venue text,
		  doi text, abstract text) ON COMMIT DROP;`); err != nil {
		return fmt.Errorf("failed to prepare OpenAlex researcher staging: %w", err)
	}
	if err := loadExtraUniversities(tx); err != nil {
		return err
	}
	if err := loadSubfieldAreas(tx); err != nil {
		return err
	}
	if _, err := copyCSVInto(tx, people, "oa_people", fieldsPeopleColumns); err != nil {
		return err
	}
	if works := openAlexFieldsPath("fields_works.csv"); fileExists(works) {
		if _, err := copyCSVInto(tx, works, "oa_works", fieldsWorksColumns); err != nil {
			return err
		}
	}
	// One row per name (the most-cited spelling's record), at a university the map knows, not
	// already a CSRankings name. professor_areas: papers per year since 2021 when works are loaded,
	// else one row for this year.
	if _, err := tx.Exec(`
		CREATE TEMP TABLE oa_kept ON COMMIT DROP AS
		SELECT DISTINCT ON (p.name) p.*
		FROM oa_people p
		WHERE p.name <> '' AND p.university IN (SELECT institution FROM universities)
		  AND p.name NOT IN (SELECT name FROM professors)
		ORDER BY p.name, NULLIF(p.cited_by, '')::int DESC NULLS LAST;

		INSERT INTO professors (name, affiliation, orcid, source, openalex_id)
		SELECT name, university, NULLIF(orcid, ''), 'openalex', openalex_id FROM oa_kept;

		-- Areas: their main subfields ('oas:<id>'), else the whole field ('oa:<id>').
		INSERT INTO professor_areas (name, affiliation, area, count, adjusted_count, year)
		SELECT k.name, k.university, a.venue, count(w.work_id)::real, count(w.work_id)::real,
		       COALESCE(NULLIF(w.year, '')::int, extract(year FROM current_date)::int)
		FROM oa_kept k
		CROSS JOIN LATERAL (
		  SELECT v.venue FROM research_area_venues v
		  WHERE v.venue IN (SELECT 'oas:' || x FROM unnest(string_to_array(NULLIF(k.subfields, ''), ';')) x)
		  UNION ALL
		  SELECT v.venue FROM research_area_venues v
		  WHERE v.area = k.area AND v.venue LIKE 'oa:%' AND COALESCE(k.subfields, '') = ''
		) a
		LEFT JOIN oa_works w ON w.openalex_id = k.openalex_id
		GROUP BY k.name, k.university, a.venue, COALESCE(NULLIF(w.year, '')::int, extract(year FROM current_date)::int)
		ON CONFLICT DO NOTHING;`); err != nil {
		return fmt.Errorf("failed to load OpenAlex researchers: %w", err)
	}
	if err := tx.Commit(); err != nil {
		return err
	}
	var n int
	_ = db.QueryRow(`SELECT count(*) FROM professors WHERE source = 'openalex'`).Scan(&n)
	logger.Infof(mainCtx, "🔬 OpenAlex researchers outside computer science: %d", n)
	return nil
}

// loadOpenAlexResearcherWorks runs after "Load DBLP Papers" (which replaces dblp_papers) and adds
// OpenAlex researchers' recent works there, newest first, capped like DBLP papers.
func loadOpenAlexResearcherWorks(mainCtx *colly.Context) error {
	people, works := openAlexFieldsPath("fields_people.csv"), openAlexFieldsPath("fields_works.csv")
	if !fileExists(people) || !fileExists(works) {
		logger.Warnf(mainCtx, "⚠️ OpenAlex researcher works not found; skipping (fields.py works)")
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
	if _, err := tx.Exec(`
		CREATE TEMP TABLE oa_people (openalex_id text, name text, university text, area text, orcid text,
		  works text, cited_by text, h_index text, subfields text) ON COMMIT DROP;
		CREATE TEMP TABLE oa_works (openalex_id text, work_id text, title text, year text, venue text,
		  doi text, abstract text) ON COMMIT DROP;`); err != nil {
		return err
	}
	if _, err := copyCSVInto(tx, people, "oa_people", fieldsPeopleColumns); err != nil {
		return err
	}
	if _, err := copyCSVInto(tx, works, "oa_works", fieldsWorksColumns); err != nil {
		return err
	}
	res, err := tx.Exec(fmt.Sprintf(`
		INSERT INTO dblp_papers (name, dblp_key, title, venue, year, url)
		SELECT name, dblp_key, title, venue, year, url FROM (
		  SELECT pr.name, 'openalex:' || w.work_id AS dblp_key, w.title, NULLIF(w.venue, '') AS venue,
		         w.year::int AS year, COALESCE(NULLIF(w.doi, ''), 'https://openalex.org/' || w.work_id) AS url,
		         row_number() OVER (PARTITION BY pr.name ORDER BY w.year DESC, w.work_id DESC) AS n
		  FROM oa_works w
		  JOIN oa_people p ON p.openalex_id = w.openalex_id
		  JOIN professors pr ON pr.name = p.name AND pr.source = 'openalex'
		  WHERE w.title <> '' AND w.year ~ '^[0-9]{4}$' AND w.title !~* $1
		) x WHERE n <= %d
		ON CONFLICT DO NOTHING`, openAlexMaxWorksPerPerson), notAPaper)
	if err != nil {
		return fmt.Errorf("failed to load OpenAlex researcher works: %w", err)
	}
	if err := tx.Commit(); err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	logger.Infof(mainCtx, "🔬 OpenAlex researcher works added to papers: %d", n)
	return nil
}

// Universities CSRankings doesn't list, chosen from OpenAlex (backup/extra_universities.csv, written by
// scripts/openalex/extra_universities.py), so their researchers have somewhere on the map to be.
var extraUniversityColumns = []string{"institution", "country", "openalex_id", "latitude", "longitude", "homepage", "source"}

func loadExtraUniversities(tx *sql.Tx) error {
	path := filepath.Join(getRootDirPath(BACKUP_DIR), "extra_universities.csv")
	if !fileExists(path) {
		return nil
	}
	if _, err := tx.Exec(`CREATE TEMP TABLE extra_unis (institution text, country text, openalex_id text,
		latitude text, longitude text, homepage text, source text) ON COMMIT DROP`); err != nil {
		return err
	}
	if _, err := copyCSVInto(tx, path, "extra_unis", extraUniversityColumns); err != nil {
		return err
	}
	_, err := tx.Exec(`
		INSERT INTO universities (institution, countryabbrv, region, latitude, longitude, homepage)
		SELECT e.institution, e.country, lower(c.region), e.latitude::double precision, e.longitude::double precision,
		       NULLIF(e.homepage, '')
		FROM extra_unis e LEFT JOIN countries c ON lower(c.alpha_2) = e.country
		ON CONFLICT (institution) DO NOTHING`)
	if err != nil {
		return fmt.Errorf("failed to add extra universities: %w", err)
	}
	return nil
}

// restoreSubfieldAreas re-adds the subfield areas after migrations (see main).
func restoreSubfieldAreas() error {
	db, err := GetDB()
	if err != nil {
		return err
	}
	tx, err := db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if err := loadSubfieldAreas(tx); err != nil {
		return err
	}
	return tx.Commit()
}

// loadSubfieldAreas adds OpenAlex subfields (data/openalex/subfields.csv) as research areas, each in
// its field's group: area 'sf<id>', venue 'oas:<id>', area_field the field's name.
func loadSubfieldAreas(tx *sql.Tx) error {
	path := openAlexFieldsPath("subfields.csv")
	if !fileExists(path) {
		return nil
	}
	if _, err := tx.Exec(`CREATE TEMP TABLE oa_subfields (subfield_id text, name text, field_id text) ON COMMIT DROP`); err != nil {
		return err
	}
	if _, err := copyCSVInto(tx, path, "oa_subfields", subfieldColumns); err != nil {
		return err
	}
	_, err := tx.Exec(`
		INSERT INTO research_area_venues (area_group, area, area_name, venue, area_field)
		SELECT f.area_group, 'sf' || s.subfield_id, s.name, 'oas:' || s.subfield_id, f.area_name
		FROM oa_subfields s JOIN research_area_venues f ON f.venue = 'oa:' || s.field_id
		ON CONFLICT (venue) DO UPDATE SET area_group = EXCLUDED.area_group, area = EXCLUDED.area,
		  area_name = EXCLUDED.area_name, area_field = EXCLUDED.area_field`)
	if err != nil {
		return fmt.Errorf("failed to add subfield areas: %w", err)
	}
	return nil
}

func fileExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}
