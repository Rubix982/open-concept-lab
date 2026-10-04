package main

import (
	"database/sql"
	"encoding/csv"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
)

// Curated university coordinates (backup/university_coordinates.csv: institution,latitude,longitude,source).
// The geocoded coordinates in universities come from matching town names and can land in the wrong
// country ("Beijing Normal University" in Normal, Illinois). server/scripts/geo/check_coordinates.py
// writes this file; the explorer build prefers it, then IPEDS coordinates, then the geocoded ones.
const universityCoordinatesFile = "university_coordinates.csv"

func loadCuratedCoordinates(tx *sql.Tx) error {
	if _, err := tx.Exec(`CREATE TEMP TABLE uc_curated (institution TEXT PRIMARY KEY, latitude REAL, longitude REAL)
		ON COMMIT DROP`); err != nil {
		return fmt.Errorf("failed to create uc_curated: %w", err)
	}
	path := filepath.Join(getRootDirPath(BACKUP_DIR), universityCoordinatesFile)
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
		if i == 0 || len(rec) < 3 {
			continue // header or incomplete row
		}
		lat, err1 := strconv.ParseFloat(rec[1], 64)
		lon, err2 := strconv.ParseFloat(rec[2], 64)
		if err1 != nil || err2 != nil {
			return fmt.Errorf("%s row %d: bad coordinates", path, i+1)
		}
		if _, err := tx.Exec(`INSERT INTO uc_curated VALUES ($1, $2, $3) ON CONFLICT (institution) DO NOTHING`,
			rec[0], lat, lon); err != nil {
			return fmt.Errorf("failed to insert curated coordinates: %w", err)
		}
	}
	return nil
}
