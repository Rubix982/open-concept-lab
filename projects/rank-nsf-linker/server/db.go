package main

import (
	"database/sql"
	"encoding/csv"
	"fmt"
	"maps"
	"os"
	"path/filepath"
	"sort"
	"strings"

	_ "github.com/lib/pq"
)

const (
	MIGRATIONS_DIR = "migrations"
	BACKUP_DIR     = "backup"
	DATA_DIR       = "data"

	POSTGRES_DRIVER = "postgres"
)

var primaryKeyAgainstTable = map[string]string{
	"countries":             "name",
	"universities":          "institution",
	"professors":            "name",
	"generated_author_info": "name",
	"geolocation":           "institution",
}

var backwardsCompatibleSchemaMap = []string{
	"countries.csv",
	"csrankings.csv",
	"geolocation.csv",
	"country-info.csv",
	"generated-author-info.csv",
}

func getPostgresConnection() (*sql.DB, error) {
	dbUrl := "postgres://postgres:postgres@localhost:5432/mydb?sslmode=disable"
	if appDbUrl := os.Getenv("DB_URL"); len(appDbUrl) > 0 {
		dbUrl = appDbUrl
	}
	db, err := sql.Open(POSTGRES_DRIVER, dbUrl)
	if err != nil {
		logger.Errorf("❌ Failed to connect to DB: %v", err)
		return nil, err
	}

	return db, nil
}

// RunMigrations executes all .sql files in order
func runMigrations() error {
	db, err := getPostgresConnection()
	if err != nil {
		logger.Fatalf("❌ Failed to connect to DB: %v", err)
		return err
	}

	defer db.Close()

	files, err := os.ReadDir(getMigrationsFilePath())
	if err != nil {
		return fmt.Errorf("cannot read migration directory: %w", err)
	}

	// Collect .sql files in sorted order
	var sqlFiles []string
	for _, file := range files {
		if strings.HasSuffix(file.Name(), ".sql") {
			sqlFiles = append(sqlFiles, file.Name())
		}
	}

	// For the order, we need to ensure that the migrations are run in the correct sequence
	sort.Strings(sqlFiles)

	for _, fname := range sqlFiles {
		path := filepath.Join(MIGRATIONS_DIR, fname)
		logger.Printf("🧩 Running migration: %s", fname)

		sqlContent, err := os.ReadFile(path)
		if err != nil {
			return fmt.Errorf("cannot read file %s: %w", fname, err)
		}

		if _, err := db.Exec(string(sqlContent)); err != nil {
			return fmt.Errorf("failed to execute migration %s: %w", fname, err)
		}

		logger.Printf("✅ Successfully ran: %s", fname)
	}

	return nil
}

func getAlternateTableName(tableName string) string {
	if tableName == "country_info" {
		return "universities"
	} else if tableName == "csrankings" {
		return "professors"
	}

	return tableName
}

func populatePostgresFromCSVs() error {
	db, err := getPostgresConnection()
	if err != nil {
		logger.Fatalf("❌ Failed to connect to DB: %v", err)
		return err
	}

	defer db.Close()

	// Process each CSV from schemaMap
	for _, csvName := range backwardsCompatibleSchemaMap {
		tableName := strings.Split(csvName, ".")[0]
		tableName = strings.ReplaceAll(tableName, "-", "_")
		tableName = getAlternateTableName(tableName)

		originalPath := filepath.Join(getDataFilePath(DATA_DIR), csvName)
		backupPath := filepath.Join(getDataFilePath(BACKUP_DIR), csvName)
		primaryKey := primaryKeyAgainstTable[tableName]

		logger.Infof("📁 Processing CSV: '%s' using primary key: '%s' with table name: '%s'",
			csvName, primaryKey, tableName)

		original, headers, err := readCSVAsMap(originalPath, primaryKey)
		if err != nil {
			logger.Errorf("❌ Failed to read original CSV: %v", err)
			return err
		}
		logger.Infof("✅ Read original CSV: %d records", len(original))

		backup := make(map[string][]string)
		if _, err := os.Stat(backupPath); err == nil {
			logger.Infof("🕒 Backup file found: %s", backupPath)
			backup, _, err = readCSVAsMap(backupPath, primaryKey)
			if err != nil {
				logger.Errorf("❌ Failed to read backup CSV: %v", err)
				return err
			}
			logger.Infof("✅ Read backup CSV: %d records", len(backup))
		} else {
			logger.Warnf("⚠️ No backup file found for: %s", backupPath)
		}

		// Merge backup + original
		merged := make(map[string][]string)
		maps.Copy(merged, backup)
		maps.Copy(merged, original)

		logger.Infof("📦 Merged total records: %d", len(merged))
		logger.Infof("⬇️ Inserting into Postgres table: %s", tableName)

		if err := insertIntoPostgres(db, tableName, headers, merged); err != nil {
			logger.Errorf("❌ Failed inserting into Postgres: %v", err)
			return err
		}

		logger.Infof("✅ Done inserting into %s\n", tableName)
	}

	return nil
}

func insertIntoPostgres(
	db *sql.DB,
	tableName string,
	headers []string,
	rows map[string][]string,
) error {
	placeholders := make([]string, len(headers))
	for i := range placeholders {
		placeholders[i] = fmt.Sprintf("$%d", i+1)
	}

	insertSQL := fmt.Sprintf("INSERT INTO %s (%s) VALUES (%s) ON CONFLICT DO NOTHING",
		tableName,
		strings.Join(headers, ", "),
		strings.Join(placeholders, ", "),
	)

	stmt, err := db.Prepare(insertSQL)
	if err != nil {
		return fmt.Errorf("failed to prepare statement: %w", err)
	}
	defer stmt.Close()

	count := 0
	for _, row := range rows {
		vals := make([]any, len(row))
		for i := range row {
			val := strings.TrimSpace(row[i])
			if val == "" {
				vals[i] = nil
			} else {
				vals[i] = val
			}
		}

		if _, err := stmt.Exec(vals...); err != nil {
			logger.Errorf("❌ Insert failed: %v. Row: %v", err, vals)
			continue
		}
		count++
	}

	logger.Infof("✅ Inserted %d rows into table %s", count, tableName)
	return nil
}

// Helper: Read CSV as map of primaryKey -> row
func readCSVAsMap(
	filePath string,
	primaryKey string,
) (map[string][]string, []string, error) {
	logger.Infof("📥 Reading CSV: %s", filePath)

	f, err := os.Open(filePath)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to open CSV: %v", err)
	}
	defer f.Close()

	reader := csv.NewReader(f)
	rows, err := reader.ReadAll()
	if err != nil {
		return nil, nil, fmt.Errorf("failed to read CSV: %v", err)
	}

	if len(rows) < 1 {
		return nil, nil, fmt.Errorf("empty CSV file")
	}

	clean := func(s string) string {
		return strings.ToLower(strings.TrimSpace(strings.ReplaceAll(s, "\uFEFF", "")))
	}

	// Clean and normalize headers
	headers := make([]string, len(rows[0]))
	for i, h := range rows[0] {
		headers[i] = clean(h)
	}

	logger.Infof("📌 Cleaned headers: %v", headers)

	index := -1
	primaryKey = clean(primaryKey)
	for i, h := range headers {
		if h == primaryKey {
			index = i
			break
		}
	}

	if index == -1 {
		return nil, nil, fmt.Errorf("primary key '%s' not found in header", primaryKey)
	}

	out := make(map[string][]string)
	skipped := 0
	for i, row := range rows[1:] {
		if len(row) != len(headers) {
			logger.Warnf("⚠️ Skipping malformed row %d: wrong length", i+1)
			skipped++
			continue
		}
		key := row[index]
		out[key] = row
	}

	if skipped > 0 {
		logger.Warnf("⚠️ Skipped %d malformed rows from %s", skipped, filePath)
	}

	return out, headers, nil
}
