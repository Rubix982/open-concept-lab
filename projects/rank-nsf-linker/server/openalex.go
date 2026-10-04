package main

import (
	"fmt"
	"os"
	"path/filepath"

	colly "github.com/gocolly/colly/v2"
)

// OpenAlex records (abstract, topic, citations) for the explorer's papers, matched by DOI.
// server/scripts/openalex/works.py writes data/openalex/works.csv; this step loads whatever is there.

var openAlexColumns = []string{"doi", "openalex_id", "abstract", "topic", "subfield", "field", "cited_by"}

func loadOpenAlexWorks(mainCtx *colly.Context) error {
	path := filepath.Join(getRootDirPath(DATA_DIR), "openalex", "works.csv")
	if _, err := os.Stat(path); err != nil {
		logger.Warnf(mainCtx, "⚠️ %s not found; skipping (see server/scripts/openalex/works.py)", path)
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
		TRUNCATE openalex_works;
		CREATE TEMP TABLE ow_stage (doi text, openalex_id text, abstract text, topic text, subfield text,
		  field text, cited_by text) ON COMMIT DROP;`); err != nil {
		return fmt.Errorf("failed to prepare OpenAlex staging: %w", err)
	}
	n, err := copyCSVInto(tx, path, "ow_stage", openAlexColumns)
	if err != nil {
		return err
	}
	if _, err := tx.Exec(`
		INSERT INTO openalex_works (doi, openalex_id, abstract, topic, subfield, field, cited_by)
		SELECT DISTINCT ON (lower(doi)) lower(doi), NULLIF(openalex_id, ''), NULLIF(abstract, ''),
		       NULLIF(topic, ''), NULLIF(subfield, ''), NULLIF(field, ''), NULLIF(cited_by, '')::int
		FROM ow_stage WHERE doi <> ''
		ORDER BY lower(doi)`); err != nil {
		return fmt.Errorf("failed to insert OpenAlex works: %w", err)
	}
	if err := tx.Commit(); err != nil {
		return err
	}
	var withAbstract int
	_ = db.QueryRow(`SELECT count(*) FROM openalex_works WHERE abstract IS NOT NULL`).Scan(&withAbstract)
	logger.Infof(mainCtx, "📖 OpenAlex: %d works loaded, %d with an abstract", n, withAbstract)
	return nil
}
