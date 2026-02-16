package main

import (
	"context"
	"database/sql"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"maps"
	"os"
	"path"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	atomic "sync/atomic"
	"time"

	colly "github.com/gocolly/colly/v2"
	pq "github.com/lib/pq"
	"github.com/lithammer/fuzzysearch/fuzzy"
	"github.com/spf13/cast"
	"golang.org/x/text/cases"
	"golang.org/x/text/language"
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
	"country-info.csv",
	"geolocation.csv",
}

var (
	globalDB *sql.DB
	initOnce sync.Once
	initErr  error
)

// InitPostgres ensures the DB is initialized only once, safely under concurrency.
func InitPostgres() (*sql.DB, error) {
	initOnce.Do(func() {
		postgresUser := os.Getenv(ENV_POSTGRES_USER)
		if len(postgresUser) == 0 {
			postgresUser = "postgres"
		}
		postgresPassword := os.Getenv(ENV_POSTGRES_PASSWORD)
		if len(postgresPassword) == 0 {
			postgresPassword = "postgres"
		}
		postgresDBName := os.Getenv(ENV_POSTGRES_DB_NAME)
		if len(postgresDBName) == 0 {
			postgresDBName = "rank-nsf-linker"
		}
		postgresHost := os.Getenv(ENV_POSTGRES_HOST)
		if len(postgresHost) == 0 {
			postgresHost = "postgres"
		}
		postgresPort := os.Getenv(ENV_POSTGRES_PORT)
		if len(postgresPort) == 0 {
			postgresPort = "5432"
		}

		dbURL := fmt.Sprintf("postgres://%s:%s@%s:%s/%s?sslmode=disable",
			postgresUser, postgresPassword, postgresHost, postgresPort, postgresDBName)

		db, err := sql.Open("postgres", dbURL)
		if err != nil {
			initErr = fmt.Errorf("failed to open DB: %w", err)
			return
		}

		// Configure the pool
		db.SetMaxOpenConns(30)                  // max total connections
		db.SetMaxIdleConns(15)                  // max idle
		db.SetConnMaxLifetime(30 * time.Minute) // recycle connections
		db.SetConnMaxIdleTime(10 * time.Minute) // optional, for cleanup

		// Verify connection
		if err := db.Ping(); err != nil {
			initErr = fmt.Errorf("failed to ping DB: %w", err)
			return
		}

		globalDB = db
	})

	return globalDB, initErr
}

// Close gracefully closes the global database connection pool.
func CloseDB(ctx *colly.Context) {
	if globalDB == nil {
		return // nothing to close
	}

	// Optionally: give it a small timeout to allow in-flight queries to finish
	dbCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Use PingContext to make sure DB is responsive before shutdown
	if err := globalDB.PingContext(dbCtx); err != nil {
		logger.Infof(ctx, "⚠️ Database not reachable during shutdown: %v", err)
	}

	if err := globalDB.Close(); err != nil {
		logger.Errorf(ctx, "❌ Failed to close database cleanly: %v", err)
	} else {
		logger.Infof(ctx, "✅ Database connection pool closed cleanly.")
	}

	globalDB = nil
}

// GetDB safely returns the global connection pool.
func GetDB() (*sql.DB, error) {
	if globalDB == nil {
		if _, err := InitPostgres(); err != nil {
			return nil, err
		}
	}
	if globalDB == nil {
		return nil, fmt.Errorf("database not initialized")
	}
	return globalDB, nil
}

// RunMigrations executes all .sql files in order
func runMigrations(ctx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

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
		logger.Infof(ctx, "🧩 Running migration: %s", fname)

		sqlContent, err := os.ReadFile(path)
		if err != nil {
			return fmt.Errorf("cannot read file %s: %w", fname, err)
		}

		if _, err := db.Exec(string(sqlContent)); err != nil {
			return fmt.Errorf("failed to execute migration %s: %w", fname, err)
		}

		logger.Infof(ctx, "✅ Successfully ran: %s", fname)
	}

	return nil
}

func getAlternateTableName(tableName string) string {
	switch tableName {
	case "country_info", "geolocation":
		return "universities"
	case "csrankings":
		return "professors"
	case "generated_author_info":
		return "professor_areas"
	}

	return tableName
}

func populatePostgresFromCSVs(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	// Process each CSV from schemaMap
	for _, csvName := range backwardsCompatibleSchemaMap {
		originalTableName := strings.Split(csvName, ".")[0]
		originalTableName = strings.ReplaceAll(originalTableName, "-", "_")
		tableName := getAlternateTableName(originalTableName)

		originalPath := filepath.Join(getRootDirPath(DATA_DIR), csvName)
		backupPath := filepath.Join(getRootDirPath(BACKUP_DIR), csvName)
		primaryKey := primaryKeyAgainstTable[tableName]

		logger.Infof(mainCtx, "📁 Processing CSV: '%s' using primary key: '%s' with table name: '%s'",
			csvName, primaryKey, tableName)

		original, headers, err := readCSVAsMap(mainCtx, originalPath, primaryKey)
		if err != nil {
			logger.Errorf(mainCtx, "❌ Failed to read original CSV: %v", err)
			return err
		}
		headers = cleanHeaders(tableName, headers)
		logger.Infof(mainCtx, "✅ Read original CSV: %d records", len(original))

		backup := make(map[string][]string)
		if _, err := os.Stat(backupPath); err == nil {
			logger.Infof(mainCtx, "🕒 Backup file found: %s", backupPath)
			backup, _, err = readCSVAsMap(mainCtx, backupPath, primaryKey)
			if err != nil {
				logger.Errorf(mainCtx, "❌ Failed to read backup CSV: %v", err)
				return err
			}
			logger.Infof(mainCtx, "✅ Read backup CSV: %d records", len(backup))
		} else {
			logger.Warnf(mainCtx, "⚠️ No backup file found for: %s", backupPath)
		}

		// Merge backup + original
		merged := make(map[string][]string)
		maps.Copy(merged, backup)
		maps.Copy(merged, original)

		logger.Infof(mainCtx, "📦 Merged total records: %d", len(merged))
		logger.Infof(mainCtx, "⬇️ Inserting into Postgres table: %s", tableName)

		if originalTableName == "geolocation" {
			/// Special case to merge country-info universities with geolocation into a single table
			for _, row := range merged {
				if _, err := db.Exec(`
	   		INSERT INTO universities (institution, latitude, longitude)
	   		VALUES ($1, $2, $3)
	   		ON CONFLICT (institution)
	   		DO UPDATE SET
	   			latitude = EXCLUDED.latitude,
	   			longitude = EXCLUDED.longitude;`, normalizeInstitutionName(row[0]), row[1], row[2]); err != nil {
					return fmt.Errorf("failed to upsert university row (institution=%s): %w", row[0], err)
				}
			}
		} else if err := insertIntoPostgres(mainCtx, db, tableName, headers, merged); err != nil {
			logger.Errorf(mainCtx, "❌ Failed inserting into Postgres: %v", err)
			return err
		}

		logger.Infof(mainCtx, "✅ Done inserting into %s\n", tableName)
	}

	return nil
}

func populatePostgresFromIpedsCSVs(mainCtx *colly.Context) error {
	dataDir := getRootDirPath(DATA_DIR)

	for year := IPEDSCurrentlyRangedYear; year <= IPEDSLatestYear; year++ {
		if err := RunIPEDSIngestion(mainCtx, dataDir, year); err != nil {
			return fmt.Errorf("failed to process ipeds download for the year '%d'. Error: %v", year, err)
		}
	}
	return nil
}

func insertIntoPostgres(
	mainCtx *colly.Context,
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

		if tableName == "universities" {
			row[0] = normalizeInstitutionName(row[0])
		}

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
			logger.Errorf(mainCtx, "❌ Insert failed: %v. Row: %v", err, vals)
			continue
		}
		count++
	}

	logger.Infof(mainCtx, "✅ Inserted %d rows into table %s", count, tableName)
	return nil
}

// Helper: Read CSV as map of primaryKey -> row
func readCSVAsMap(
	mainCtx *colly.Context,
	filePath string,
	primaryKey string,
) (map[string][]string, []string, error) {
	logger.Infof(mainCtx, "📥 Reading CSV: %s", filePath)

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

	logger.Infof(mainCtx, "📌 Cleaned headers: %v", headers)

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
			logger.Warnf(mainCtx, "⚠️ Skipping malformed row %d: wrong length", i+1)
			skipped++
			continue
		}
		key := row[index]
		out[key] = row
	}

	if skipped > 0 {
		logger.Warnf(mainCtx, "⚠️ Skipped %d malformed rows from %s", skipped, filePath)
	}

	return out, headers, nil
}

func populatePostgresFromNsfJsons(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	internalContainerPath := path.Join(getRootDirPath(DATA_DIR), NSF_DATA_DIR)
	logger.Infof(mainCtx, "🚀 Starting NSF JSON population from: %s", internalContainerPath)

	var wg sync.WaitGroup

	for year := NSFAwardsEndYear; year >= NSFAwardsStartYear; year-- {
		wg.Add(1)

		go func(year int) {
			defer wg.Done()
			processNsfAwardPerYear(mainCtx, internalContainerPath, year, db)
		}(year)
	}

	wg.Wait()

	logger.Infof(mainCtx, "🎉 NSF JSON population completed successfully.")
	return nil
}

func processNsfAwardPerYear(
	mainCtx *colly.Context,
	internalContainerPath string,
	year int,
	db *sql.DB,
) {
	path := filepath.Join(internalContainerPath, fmt.Sprintf("%d", year))
	files, err := os.ReadDir(path)
	if err != nil {
		logger.Errorf(mainCtx, "❌ Failed to read directory %s: %v", path, err)
		return
	}

	logger.Infof(mainCtx, "📂 Processing %d JSON files for year %d", len(files), year)
	var nsfJsonData NsfJsonData

	for _, file := range files {
		filePath := filepath.Join(path, file.Name())
		rawBytes, err := os.ReadFile(filePath)
		if err != nil {
			logger.Warnf(mainCtx, "⚠️  Skipping file (read error): %s (%v)", filePath, err)
			continue
		}

		if err := json.Unmarshal(rawBytes, &nsfJsonData); err != nil {
			logger.Warnf(mainCtx, "⚠️  Skipping file (parse error): %s (%v)", filePath, err)
			continue
		}

		logger.Infof(mainCtx, "➡️  Processing award: %s", nsfJsonData.AwdId)
		nsfJsonData = cleanNsfJsonData(nsfJsonData)
		region, countryabbrv := getRegionAndCountry(nsfJsonData.Institute.Country)

		universityUpsertQuery := `
				INSERT INTO universities (institution, street_address, city, phone, zip_code, country, region, countryabbrv)
				VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
				ON CONFLICT (institution) DO UPDATE SET
					street_address = EXCLUDED.street_address,
					city = EXCLUDED.city,
					phone = EXCLUDED.phone,
					zip_code = EXCLUDED.zip_code,
					country = EXCLUDED.country;
			`
		institute := nsfJsonData.Institute
		originalInstName := institute.Name
		institute.Name = normalizeInstitutionName(institute.Name)
		_, err = db.Exec(universityUpsertQuery, institute.Name, institute.StreetAddress,
			institute.City, institute.PhoneNumber, institute.ZipCode, institute.Country,
			region, countryabbrv)
		if err != nil {
			logger.Warnf(mainCtx, "⚠️  University upsert failed (%s, normalized '%s'): %v", originalInstName, institute.Name, err)
			continue
		}

		directorateDivQuery := `
				INSERT INTO directorate_division (directorate_abbr, directorate_name, division_abbr, division_name)
				VALUES ($1, $2, $3, $4)
				ON CONFLICT (directorate_abbr, division_abbr)
				DO UPDATE SET directorate_abbr = EXCLUDED.directorate_abbr
				RETURNING id;
			`
		var directorateDivisionId string
		err = db.QueryRow(directorateDivQuery, nsfJsonData.DirectorateAbbreviation,
			nsfJsonData.OrganizationDirectorateLongName, nsfJsonData.DivisionAbbreviation,
			nsfJsonData.OrganizationDivisionLongName).Scan(&directorateDivisionId)
		if err != nil {
			logger.Warnf(mainCtx, "⚠️  Directorate/division upsert failed: %v", err)
			continue
		}

		programOfficerQuery := `
				INSERT INTO program_officer (name, phone, email)
				VALUES ($1, $2, $3)
				ON CONFLICT (name) DO UPDATE SET
					phone = EXCLUDED.phone,
					email = EXCLUDED.email
				RETURNING id;
			`
		var programOfficerId string
		err = db.QueryRow(programOfficerQuery, nsfJsonData.PoSignBlockName,
			nsfJsonData.PoPhoneNumber, nsfJsonData.PoEmailNumber).Scan(&programOfficerId)
		if err != nil {
			logger.Warnf(mainCtx, "⚠️  Program officer upsert failed: %v", err)
			continue
		}

		awardInsertQuery := `
				INSERT INTO award (
					id, year, award_agency_id, transaction_type, award_instrument_text, award_title_text, cfda_number,
					org_code, program_officer_id, award_effective_date, award_expiry_date, total_international_award_amount,
					award_amount, earliest_amendment_date, most_recent_amendment_date, abstract, arra_award,
					directorate_division_id, award_agency_code, fund_agency_code, institution, performing_institution,
					html_content, raw_content
				)
				VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24)
				ON CONFLICT (id) DO UPDATE SET
					year = EXCLUDED.year,
					award_agency_id = EXCLUDED.award_agency_id,
					transaction_type = EXCLUDED.transaction_type,
					award_instrument_text = EXCLUDED.award_instrument_text,
					award_title_text = EXCLUDED.award_title_text,
					cfda_number = EXCLUDED.cfda_number,
					org_code = EXCLUDED.org_code,
					program_officer_id = EXCLUDED.program_officer_id,
					award_effective_date = EXCLUDED.award_effective_date,
					award_expiry_date = EXCLUDED.award_expiry_date,
					total_international_award_amount = EXCLUDED.total_international_award_amount,
					award_amount = EXCLUDED.award_amount,
					earliest_amendment_date = EXCLUDED.earliest_amendment_date,
					most_recent_amendment_date = EXCLUDED.most_recent_amendment_date,
					abstract = EXCLUDED.abstract,
					arra_award = EXCLUDED.arra_award,
					directorate_division_id = EXCLUDED.directorate_division_id,
					award_agency_code = EXCLUDED.award_agency_code,
					fund_agency_code = EXCLUDED.fund_agency_code,
					institution = EXCLUDED.institution,
					performing_institution = EXCLUDED.performing_institution;
			`

		htmlContent, rawContent := "", ""
		if nsfJsonData.ProjectOutcomesReport != nil {
			htmlContent = nsfJsonData.ProjectOutcomesReport.HtmlContent
			rawContent = nsfJsonData.ProjectOutcomesReport.RawText
		}

		awardValues := []any{
			nsfJsonData.AwdId, year, nsfJsonData.AwardingAgencyCode, nsfJsonData.TranType,
			nsfJsonData.AwardInstrumentText, nsfJsonData.AwardTitleText,
			nsfJsonData.FederalCatalogDomesticAssistanceNumber, nsfJsonData.OrgCode,
			programOfficerId, nsfJsonData.AwardEffectiveDate, nsfJsonData.AwardExpiryDate,
			nsfJsonData.TotalIntendedAwardAmount, nsfJsonData.AwardAmount,
			nsfJsonData.EarliestAmendmentDate, nsfJsonData.MostRecentAmendmentDate,
			nsfJsonData.AwardAbstract, nsfJsonData.AwardARRA, directorateDivisionId,
			nsfJsonData.AwardingAgencyCode, nsfJsonData.FundingAgencyCode,
			institute.Name, institute.Name, htmlContent, rawContent,
		}
		if _, err = db.Exec(awardInsertQuery, awardValues...); err != nil {
			logger.Warnf(mainCtx, "⚠️  Award upsert failed (%s): %v", nsfJsonData.AwdId, err)
			continue
		}

		for _, pe := range nsfJsonData.ProgramElements {
			if _, err = db.Exec(`
					INSERT INTO program_element (award_id, code, name)
					VALUES ($1, $2, $3)
					ON CONFLICT (award_id, code) DO UPDATE SET name = EXCLUDED.name;
				`, nsfJsonData.AwdId, pe.ProgramElementCode, pe.ProgramElementName); err != nil {
				logger.Warnf(mainCtx, "⚠️  Program element upsert failed: %v", err)
			}
		}

		for _, pr := range nsfJsonData.ProgramReference {
			if _, err = db.Exec(`
					INSERT INTO program_reference (award_id, code, name)
					VALUES ($1, $2, $3)
					ON CONFLICT (award_id, code) DO UPDATE SET name = EXCLUDED.name;
				`, nsfJsonData.AwdId, pr.ProgramReferenceCode, pr.ProgramReferenceName); err != nil {
				logger.Warnf(mainCtx, "⚠️  Program reference upsert failed: %v", err)
			}
		}

		for _, af := range nsfJsonData.ApplicationFunding {
			if _, err = db.Exec(`
					INSERT INTO application_funding (award_id, code, name, symbol_id, funding_code, funding_name, funding_symbol_id)
					VALUES ($1, $2, $3, $4, $5, $6, $7)
					ON CONFLICT (award_id, code) DO UPDATE SET name = EXCLUDED.name, symbol_id = EXCLUDED.symbol_id;
				`, nsfJsonData.AwdId, af.ApplicationCode, af.ApplicationName, af.ApplicationSymbolId, af.FundingCode, af.FundingName, af.FundingSymbolId); err != nil {
				logger.Warnf(mainCtx, "⚠️  Application funding upsert failed: %v", err)
			}
		}

		for _, fy := range nsfJsonData.FundingObligations {
			if _, err = db.Exec(`
					INSERT INTO fiscal_year_funding (award_id, fiscal_year, funding_amount)
					VALUES ($1, $2, $3)
					ON CONFLICT (award_id, fiscal_year) DO UPDATE SET funding_amount = EXCLUDED.funding_amount;
				`, nsfJsonData.AwdId, fy.FiscalYear, fy.AmountObligated); err != nil {
				logger.Warnf(mainCtx, "⚠️  Fiscal year funding upsert failed: %v", err)
			}
		}

		for _, pi := range nsfJsonData.PrincipalInvestigators {
			if _, err = db.Exec(`
					INSERT INTO professors (name, affiliation, nsf_id)
					VALUES ($1, $2, $3)
					ON CONFLICT (name) DO UPDATE SET nsf_id = EXCLUDED.nsf_id;
				`, pi.Name, normalizeInstitutionName(nsfJsonData.PerformingInsitute.InstituteName), pi.NSFId); err != nil {
				logger.Warnf(mainCtx, "⚠️  Professor upsert failed: %v", err)
			}

			if _, err = db.Exec(`
					INSERT INTO award_pi_rel (award_id, investigator_id, pi_role, pi_start_date, pi_end_date)
					VALUES ($1, $2, $3, $4, $5)
					ON CONFLICT (award_id, investigator_id) DO UPDATE SET
						pi_role = EXCLUDED.pi_role,
						pi_start_date = EXCLUDED.pi_start_date,
						pi_end_date = EXCLUDED.pi_end_date;
				`, nsfJsonData.AwdId, pi.Name, pi.Role, pi.StartDate, pi.EndDate); err != nil {
				logger.Warnf(mainCtx, "⚠️  Award-PI relationship upsert failed: %v", err)
			}
		}

		logger.Infof(mainCtx, "✅ Successfully processed award %s (%d)", nsfJsonData.AwdId, year)
	}
}

func ToTitleCase(str string) string {
	return cases.Title(language.English).String(strings.TrimSpace(str))
}

func cleanHeaders(
	tableName string,
	headers []string,
) []string {
	switch tableName {
	case "professors":
		for i, h := range headers {
			if h == "scholarid" {
				headers[i] = "scholar_id"
			}
		}
	case "professor_areas":
		for i, h := range headers {
			if h == "dept" {
				headers[i] = "affiliation"
			}
		}
	}

	return headers
}

func cleanNsfJsonData(data NsfJsonData) NsfJsonData {
	data.Institute.Name = ToTitleCase(data.Institute.Name)
	data.PerformingInsitute.InstituteName = ToTitleCase(data.PerformingInsitute.InstituteName)
	if data.AwardInstrumentText == "Fellowship Award" {
		data.Institute.Name = data.PerformingInsitute.InstituteName
	}
	data.Institute.StreetAddress = data.Institute.StreetAddress + " " + data.Institute.StreetAddressV2
	data.Institute.StreetAddress = ToTitleCase(data.Institute.StreetAddress)
	data.Institute.City = ToTitleCase(data.Institute.City)
	return data
}

func getRegionAndCountry(country string) (string, string) {
	switch country {
	case "Germany":
		return "europe", "gr"
	case "France":
		return "europe", "fr"
	case "United Kingdom":
		return "europe", "gb"
	case "Canada":
		return "northamerica", "ca"
	case "United States":
		return "northamerica", "us"
	case "Australia":
		return "oceania", "au"
	case "New Zealand":
		return "oceania", "nz"
	case "Uruguay":
		return "southamerica", "uy"
	case "Brazil":
		return "southamerica", "br"
	default:
		return "northamerica", "us"
	}
}

func populatePostgresFromScriptCaches(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	internalContainerPath := path.Join(getRootDirPath(SCRIPTS_DIR), GEOCODING_DIR)
	logger.Infof(mainCtx, "🚀 Starting script cache population from: %s", internalContainerPath)

	// Paths
	geoCodedCachePath := path.Join(internalContainerPath, "geocoded_cache.csv")
	reverseGeoCodedCachePath := path.Join(internalContainerPath, "reverse_geocoded_cache.csv")

	// 1️⃣ Handle geocoded cache first
	if err := syncCSVToDB(mainCtx, db, geoCodedCachePath); err != nil {
		logger.Errorf(mainCtx, "❌ Failed to sync geocoded cache: %v", err)
		return err
	}

	// 2️⃣ Then reverse-geocoded cache
	if err := syncCSVToDB(mainCtx, db, reverseGeoCodedCachePath); err != nil {
		logger.Errorf(mainCtx, "❌ Failed to sync reverse geocoded cache: %v", err)
		return err
	}

	logger.Infof(mainCtx, "✅ Completed populating script caches into Postgres")
	return nil
}

// syncCSVToDB reads a CSV file and upserts it into the given table
func syncCSVToDB(
	mainCtx *colly.Context,
	db *sql.DB,
	filePath string,
) error {
	file, err := os.Open(filePath)
	if err != nil {
		return fmt.Errorf("failed to open file %s: %w", filePath, err)
	}

	defer file.Close()

	reader := csv.NewReader(file)
	reader.TrimLeadingSpace = true
	records, err := reader.ReadAll()
	if err != nil {
		return fmt.Errorf("failed to read CSV %s: %w", filePath, err)
	}

	if len(records) < 1 {
		logger.Warnf(mainCtx, "⚠️ CSV %s is empty, skipping", filePath)
		return nil
	}

	header := records[0]
	logger.Infof(mainCtx, "📄 Found %d rows (excluding header) in %s", len(records)-1, filepath.Base(filePath))

	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to start transaction: %w", err)
	}

	defer tx.Rollback()

	insertQuery := buildUpsertQuery(header)
	stmt, err := tx.Prepare(insertQuery)
	if err != nil {
		return fmt.Errorf("failed to prepare upsert: %w", err)
	}

	defer stmt.Close()

	for i, row := range records[1:] {
		args := make([]any, len(row))
		for j, val := range row {
			args[j] = strings.TrimSpace(val)
		}

		if _, err := stmt.Exec(args...); err != nil {
			logger.Warnf(mainCtx, "⚠️ Row %d failed to insert: %v", i+2, err)
			continue
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	logger.Infof(mainCtx, "✅ Synced %s into database successfully", filepath.Base(filePath))
	return nil
}

// buildUpsertQuery dynamically builds a Postgres UPSERT query
func buildUpsertQuery(columns []string) string {
	colList := strings.Join(columns, ", ")
	paramList := make([]string, len(columns))
	updateList := make([]string, len(columns))
	for i := range columns {
		if columns[i] == "institution" {
			columns[i] = normalizeInstitutionName(columns[i])
		}
		paramList[i] = fmt.Sprintf("$%d", i+1)
		updateList[i] = fmt.Sprintf("%s = EXCLUDED.%s", columns[i], columns[i])
	}

	return fmt.Sprintf(`
		INSERT INTO universities (%s)
		VALUES (%s)
		ON CONFLICT (%s)
		DO UPDATE SET %s;
	`, colList, strings.Join(paramList, ", "), columns[0], strings.Join(updateList, ", "))
}

func clearFinalDataStatesInPostgres(mainCtx *colly.Context) error {
	// Select all rows from the table 'universities' where 'region' or 'countryabbrv' is null
	// Check the 'country' column value, and update the two values appropriately
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	regionCountryAbbrvQueryUpdate := `
	UPDATE universities
	SET 
		region = CASE
			WHEN country = 'United States' THEN 'northamerica'
			WHEN country = 'Canada' THEN 'northamerica'
			WHEN country = 'Germany' THEN 'europe'
			WHEN country = 'Japan' THEN 'asia'
			WHEN country = 'Australia' THEN 'oceania'
			ELSE region
		END,
		countryabbrv = CASE
			WHEN country = 'United States' THEN 'us'
			WHEN country = 'Canada' THEN 'ca'
			WHEN country = 'Germany' THEN 'de'
			WHEN country = 'Japan' THEN 'jp'
			WHEN country = 'Australia' THEN 'au'
			ELSE countryabbrv
		END
	WHERE region IS NULL OR countryabbrv IS NULL;`

	_, err = db.Exec(regionCountryAbbrvQueryUpdate)
	if err != nil {
		return fmt.Errorf("failed to update universities table: %w", err)
	}

	logger.Infof(mainCtx, "✅ Cleared final data states in Postgres successfully")

	return nil
}

func populateHomepagesAgainstUniversities(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	// Step 1. Load universities from DB into memory
	rows, err := db.Query(`SELECT institution FROM universities`)
	if err != nil {
		return fmt.Errorf("failed to load universities: %v", err)
	}
	defer rows.Close()

	universities := make(map[string]bool)
	var universityList []string
	for rows.Next() {
		var inst string
		if err := rows.Scan(&inst); err == nil {
			universities[normalizeInstitutionName(inst)] = true
			universityList = append(universityList, normalizeInstitutionName(inst))
		}
	}

	// Step 2. Read CSV
	file, err := os.Open(filepath.Join(getRootDirPath(BACKUP_DIR), UNI_AGNST_WEBURL))
	if err != nil {
		return fmt.Errorf("failed to open CSV: %v", err)
	}
	defer file.Close()

	reader := csv.NewReader(file)
	reader.FieldsPerRecord = -1
	records, err := reader.ReadAll()
	if err != nil {
		return fmt.Errorf("failed to read CSV: %v", err)
	}

	type updatePair struct {
		homepage    string
		institution string
	}

	var updates []updatePair
	var updated, skipped, fuzzyMatched int

	// Step 3. Match in memory
	for _, row := range records {
		if len(row) < 2 {
			skipped++
			continue
		}

		rawInst := strings.TrimSpace(row[0])
		homepage := strings.TrimSpace(row[1])
		if rawInst == "" || homepage == "" {
			skipped++
			continue
		}

		normInst := normalizeInstitutionName(rawInst)
		match := normInst

		if !universities[normInst] {
			// fuzzy fallback
			best := fuzzy.RankFindNormalized(normInst, universityList)
			if len(best) == 0 || best[0].Distance > 10 { // tune distance
				skipped++
				continue
			}
			match = universityList[best[0].OriginalIndex]
			fuzzyMatched++
		}

		updates = append(updates, updatePair{homepage: homepage, institution: match})
		updated++
	}

	// Step 4. Bulk update with transaction
	tx, err := db.Begin()
	if err != nil {
		return err
	}
	stmt, err := tx.Prepare(`UPDATE universities SET homepage = $1 WHERE institution = $2`)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for _, u := range updates {
		if _, err := stmt.Exec(u.homepage, u.institution); err != nil {
			logger.Warnf(mainCtx, "⚠️ Failed to update %s: %v", u.institution, err)
		}
	}
	if err := tx.Commit(); err != nil {
		return err
	}

	logger.Infof(mainCtx, "✅ Updated %d institutions (%d fuzzy matched, %d skipped)", updated, fuzzyMatched, skipped)
	return nil
}

func syncProfessorsAffiliationsToUniversities(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	// We need to iterate over all the professors
	rows, err := db.Query(`SELECT name, affiliation FROM professors`)
	if err != nil {
		return fmt.Errorf("failed to query professors table: %w", err)
	}

	defer rows.Close()

	var professors []map[string]string

	for rows.Next() {
		var name, affiliation string
		if err := rows.Scan(&name, &affiliation); err != nil {
			logger.Warnf(mainCtx, "⚠️ Failed to scan professor row: %v", err)
			continue
		}
		professors = append(professors, map[string]string{
			"name":        name,
			"affiliation": affiliation,
		})
	}

	sem := make(chan struct{}, 20)
	var wg sync.WaitGroup

	var updated, skipped int64

	for _, prof := range professors {
		wg.Add(1)
		sem <- struct{}{}

		go func(prof map[string]string) {
			defer wg.Done()
			defer func() { <-sem }()

			affiliation := prof["affiliation"]
			if affiliation == "" {
				atomic.AddInt64(&skipped, 1)
				return
			}
			profName := prof["name"]
			if profName == "" {
				atomic.AddInt64(&skipped, 1)
				return
			}

			// Fuzzy match affiliation against universities
			normalizedAffiliation := normalizeInstitutionName(affiliation)

			var matchedInstitution string
			err = db.QueryRow(`
				SELECT institution
				FROM universities
				WHERE institution % $1
				ORDER BY similarity(institution, $1) DESC
				LIMIT 1
			`, normalizedAffiliation).Scan(&matchedInstitution)

			if err == sql.ErrNoRows {
				logger.Warnf(mainCtx, "⚠️ No match found for professor '%s' with affiliation '%s'", profName, affiliation)
				// We should insert the affiliation as a new university
				_, insertErr := db.Exec(`INSERT INTO universities (institution) VALUES ($1) ON CONFLICT (institution) DO NOTHING;`, normalizedAffiliation)
				if insertErr != nil {
					logger.Warnf(mainCtx, "⚠️ Failed to insert new university for affiliation '%s': %v", normalizedAffiliation, insertErr)
					atomic.AddInt64(&skipped, 1)
					return
				}
				matchedInstitution = normalizedAffiliation
				logger.Infof(mainCtx, "➕ Added new university for affiliation '%s'", normalizedAffiliation)
			} else if err != nil {
				logger.Warnf(mainCtx, "⚠️ Fuzzy match failed for professor '%s' with affiliation '%s': %v", profName, affiliation, err)
				atomic.AddInt64(&skipped, 1)
				return
			}

			if err != nil {
				logger.Warnf(mainCtx, "⚠️ Fuzzy match failed for professor '%s' with affiliation '%s': %v", profName, affiliation, err)
				atomic.AddInt64(&skipped, 1)
				return
			}

			// Update professor's affiliation to the matched institution
			_, err = db.Exec(`UPDATE professors SET affiliation = $1 WHERE name = $2`, matchedInstitution, profName)
			if err != nil {
				logger.Warnf(mainCtx, "⚠️ Failed to update professor '%s' affiliation: %v", profName, err)
				atomic.AddInt64(&skipped, 1)
				return
			}

			atomic.AddInt64(&updated, 1)
		}(prof)
	}

	wg.Wait()

	logger.Infof(mainCtx, "✅ Synchronized affiliations for %d professors (%d skipped)", updated, skipped)

	return nil
}

func syncProfessorInterestsToProfessorsAndUniversities(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	db.SetMaxOpenConns(100)
	db.SetMaxIdleConns(50)
	db.SetConnMaxLifetime(time.Minute * 10)

	file, err := os.Open(filepath.Join(getRootDirPath(DATA_DIR), GEN_AUTHOR_FILENAME))
	if err != nil {
		return fmt.Errorf("failed to open CSV: %v", err)
	}
	defer file.Close()

	reader := csv.NewReader(file)

	// Create a temporary staging table
	_, err = db.Exec(`
        CREATE TABLE IF NOT EXISTS staging_professor_areas (
            name TEXT,
            affiliation TEXT,
            area TEXT,
            count DOUBLE PRECISION,
            adjusted_count DOUBLE PRECISION,
            year INT
        );
    `)
	if err != nil {
		return fmt.Errorf("failed to create staging table: %v", err)
	}

	defer func() {
		_, err := db.Exec(`DROP TABLE IF EXISTS staging_professor_areas;`)
		if err != nil {
			logger.Warnf(mainCtx, "⚠️ Failed to drop staging table: %v", err)
		}
	}()

	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to start transaction: %v", err)
	}

	stmt, err := tx.Prepare(pq.CopyIn("staging_professor_areas", "name", "affiliation", "area",
		"count", "adjusted_count", "year"))
	if err != nil {
		return fmt.Errorf("failed to prepare COPY statement: %v", err)
	}

	const batchSize = 5000
	var batch [][]interface{}
	var validRows int

	for {
		row, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			logger.Warnf(mainCtx, "⚠️ Skipping invalid row: %v", err)
			continue
		}

		if len(row) < 6 || strings.TrimSpace(row[0]) == "name" {
			continue
		}

		name := strings.TrimSpace(row[0])
		affiliation := strings.TrimSpace(row[1])
		area := strings.TrimSpace(row[2])
		count := strings.TrimSpace(row[3])
		adjustedCount := strings.TrimSpace(row[4])
		year := strings.TrimSpace(row[5])

		if name == "" || affiliation == "" || area == "" || count == "" || adjustedCount == "" || year == "" {
			logger.Warnf(mainCtx, "⚠️ Skipped invalid row: %v", row)
			continue
		}

		normalizedAffiliation := normalizeInstitutionName(affiliation)
		batch = append(batch, []interface{}{name, normalizedAffiliation, area, count, adjustedCount, year})
		validRows++

		if len(batch) >= batchSize {
			for _, r := range batch {
				if _, err := stmt.Exec(r...); err != nil {
					logger.Warnf(mainCtx, "⚠️ Failed to add row to staging table: %v", err)
				}
			}
			batch = batch[:0]
		}
	}

	// Insert remaining rows
	for _, r := range batch {
		if _, err := stmt.Exec(r...); err != nil {
			logger.Warnf(mainCtx, "⚠️ Failed to add row to staging table: %v", err)
		}
	}

	if _, err = stmt.Exec(); err != nil {
		return fmt.Errorf("failed to finalize COPY: %v", err)
	}

	if err = stmt.Close(); err != nil {
		return fmt.Errorf("failed to close COPY statement: %v", err)
	}

	if err = tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %v", err)
	}

	logger.Infof(mainCtx, "✅ Copied %d valid rows into staging table", validRows)

	// Batch UPSERT into final table
	const upsertBatchSize = 1000
	offset := 0

	for {
		rows, err := db.Query(`
            SELECT s.name, s.affiliation, s.area, s.count, s.adjusted_count, s.year
            FROM staging_professor_areas s
            ORDER BY s.name
            OFFSET $1 LIMIT $2
        `, offset, upsertBatchSize)
		if err != nil {
			return fmt.Errorf("failed to fetch staging batch: %v", err)
		}

		batchCount := 0
		txUpsert, err := db.Begin()
		if err != nil {
			return fmt.Errorf("failed to start upsert transaction: %v", err)
		}

		stmtUpsert, err := txUpsert.Prepare(`
            INSERT INTO professor_areas (name, affiliation, area, count, adjusted_count, year)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (name, affiliation, area, year)
            DO UPDATE SET
                count = EXCLUDED.count,
                adjusted_count = EXCLUDED.adjusted_count;
        `)
		if err != nil {
			return fmt.Errorf("failed to prepare upsert statement: %v", err)
		}

		for rows.Next() {
			var name, affiliation, area string
			var count, adjustedCount float64
			var year int

			if err := rows.Scan(&name, &affiliation, &area, &count, &adjustedCount, &year); err != nil {
				logger.Warnf(mainCtx, "⚠️ Failed to scan row for upsert: %v", err)
				continue
			}

			if _, err := stmtUpsert.Exec(name, affiliation, area, count, adjustedCount, year); err != nil {
				logger.Warnf(mainCtx, "⚠️ Failed to upsert row: %v", err)
				continue
			}
			batchCount++
		}

		if err := stmtUpsert.Close(); err != nil {
			return fmt.Errorf("failed to close upsert statement: %v", err)
		}

		if err := txUpsert.Commit(); err != nil {
			return fmt.Errorf("failed to commit upsert transaction: %v", err)
		}

		rows.Close()

		if batchCount == 0 {
			break
		}
		offset += batchCount
	}

	logger.Infof(mainCtx, "✅ Synchronized professor interests successfully from CSV")
	return nil
}

// identifyCanonicalUniversity selects the canonical name from a list of university name variants.
// It prefers full names over abbreviated ones and avoids department-specific names.
func identifyCanonicalUniversity(variants []string) string {
	if len(variants) == 0 {
		return ""
	}

	// Score each variant based on quality indicators
	type scoredVariant struct {
		name  string
		score int
	}

	overrideMap := map[string]string{
		"Carnegie - Mellon University": "Carnegie Mellon University",
	}

	var scored []scoredVariant
	for _, variant := range variants {
		score := 0
		lower := strings.ToLower(variant)

		// Prefer longer names (more complete)
		score += len(variant)

		// Penalize abbreviations
		if strings.Contains(lower, "univ.") || strings.Contains(lower, "dept") {
			score -= 50
		}

		// Penalize department/lab specific names
		if strings.Contains(lower, "department of") || strings.Contains(lower, "dept of") ||
			strings.Contains(lower, "lab") || strings.Contains(lower, "institute of") ||
			strings.Contains(lower, "scripps") || strings.Contains(lower, "marine science") {
			score -= 100
		}

		// Prefer "University of" format over "Univ of" or "U.c."
		if strings.HasPrefix(lower, "university of") || strings.HasPrefix(lower, "the university of") {
			score += 30
		}

		// Penalize "The" prefix slightly (less canonical)
		if strings.HasPrefix(lower, "the ") {
			score -= 5
		}

		// Prefer comma-separated format (e.g., "University of California, Berkeley")
		if strings.Count(variant, ",") == 1 {
			score += 20
		}

		scored = append(scored, scoredVariant{name: variant, score: score})
	}

	// Sort by score descending
	sort.Slice(scored, func(i, j int) bool {
		return scored[i].score > scored[j].score
	})

	scoredName := scored[0].name

	if overrideName := overrideMap[scoredName]; overrideName != "" {
		return overrideName
	}

	return scoredName
}

// buildUniversityNormalizationMap creates a mapping of variant university names to their canonical forms.
// It analyzes the duplicate lists and identifies the best canonical name for each group.
func buildUniversityNormalizationMap(duplicateGroups map[string][]string) map[string]string {
	normalizationMap := make(map[string]string)

	for _, variants := range duplicateGroups {
		if len(variants) == 0 {
			continue
		}

		// Identify the canonical name for this group
		canonical := identifyCanonicalUniversity(variants)

		// Map all variants to the canonical name
		for _, variant := range variants {
			if variant != canonical {
				normalizationMap[variant] = canonical
			}
		}
	}

	return normalizationMap
}

// normalizeUniversityReferences updates all foreign key references to use canonical university names.
// This ensures data consistency before removing duplicate university entries.
func normalizeUniversityReferences(mainCtx *colly.Context, normalizationMap map[string]string) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	if len(normalizationMap) == 0 {
		logger.Infof(mainCtx, "ℹ️ No university name normalization needed")
		return nil
	}

	// Start a transaction for atomicity
	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	var totalUpdated int64

	// Update award.institution
	for variant, canonical := range normalizationMap {
		result, err := tx.Exec(`UPDATE award SET institution = $1 WHERE institution = $2`, canonical, variant)
		if err != nil {
			return fmt.Errorf("failed to update award.institution from '%s' to '%s': %w", variant, canonical, err)
		}
		rowsAffected, _ := result.RowsAffected()
		if rowsAffected > 0 {
			logger.Infof(mainCtx, "🔄 Updated %d award.institution references: '%s' → '%s'", rowsAffected, variant, canonical)
			totalUpdated += rowsAffected
		}
	}

	// Update award.performing_institution
	for variant, canonical := range normalizationMap {
		result, err := tx.Exec(`UPDATE award SET performing_institution = $1 WHERE performing_institution = $2`, canonical, variant)
		if err != nil {
			return fmt.Errorf("failed to update award.performing_institution from '%s' to '%s': %w", variant, canonical, err)
		}
		rowsAffected, _ := result.RowsAffected()
		if rowsAffected > 0 {
			logger.Infof(mainCtx, "🔄 Updated %d award.performing_institution references: '%s' → '%s'", rowsAffected, variant, canonical)
			totalUpdated += rowsAffected
		}
	}

	// Update professor_areas.affiliation
	for variant, canonical := range normalizationMap {
		// Create savepoint before risky operation
		_, err := tx.Exec(`SAVEPOINT before_update`)
		if err != nil {
			return fmt.Errorf("failed to create savepoint: %w", err)
		}

		result, err := tx.Exec(`UPDATE professor_areas SET affiliation = $1 WHERE affiliation = $2`, canonical, variant)
		if err != nil {
			if strings.Contains(err.Error(), "duplicate key value violates unique constraint") {
				// Rollback to savepoint (clears the error state)
				_, rollbackErr := tx.Exec(`ROLLBACK TO SAVEPOINT before_update`)
				if rollbackErr != nil {
					return fmt.Errorf("failed to rollback to savepoint: %w", rollbackErr)
				}

				logger.Infof(mainCtx, "ℹ️  Duplicate constraint for '%s', cleaning up...", variant)

				// Now we can execute commands again
				deleteQuery := `
                WITH duplicates AS (
                    SELECT DISTINCT pa1.name, pa1.area
                    FROM professor_areas pa1
                    INNER JOIN professor_areas pa2 
                      ON pa1.name = pa2.name
                     AND pa1.area = pa2.area
                    WHERE pa1.affiliation = $1
                      AND pa2.affiliation = $2
                )
                DELETE FROM professor_areas
                WHERE affiliation = $1
                  AND (name, area) IN (SELECT * FROM duplicates)
            `

				delResult, err := tx.Exec(deleteQuery, variant, canonical)
				if err != nil {
					return fmt.Errorf("failed to delete duplicates: %w", err)
				}

				deleted, _ := delResult.RowsAffected()
				logger.Infof(mainCtx, "🗑️  Deleted %d duplicate rows with affiliation '%s'", deleted, variant)

				// Retry the UPDATE
				result, err = tx.Exec(`UPDATE professor_areas SET affiliation = $1 WHERE affiliation = $2`, canonical, variant)
				if err != nil {
					return fmt.Errorf("retry update failed: %w", err)
				}

				// Release savepoint (cleanup)
				_, _ = tx.Exec(`RELEASE SAVEPOINT before_update`)
			} else {
				return fmt.Errorf("failed to update professor_areas.affiliation: %w", err)
			}
		} else {
			// Success - release savepoint
			_, _ = tx.Exec(`RELEASE SAVEPOINT before_update`)
		}

		rowsAffected, _ := result.RowsAffected()
		if rowsAffected > 0 {
			logger.Infof(mainCtx, "🔄 Updated %d professor_areas.affiliation: '%s' → '%s'", rowsAffected, variant, canonical)
			totalUpdated += rowsAffected
		}
	}

	// Update professors.affiliation
	for variant, canonical := range normalizationMap {
		result, err := tx.Exec(`UPDATE professors SET affiliation = $1 WHERE affiliation = $2`, canonical, variant)
		if err != nil {
			return fmt.Errorf("failed to update professors.affiliation from '%s' to '%s': %w", variant, canonical, err)
		}
		rowsAffected, _ := result.RowsAffected()
		if rowsAffected > 0 {
			logger.Infof(mainCtx, "🔄 Updated %d professors.affiliation references: '%s' → '%s'", rowsAffected, variant, canonical)
			totalUpdated += rowsAffected
		}
	}

	// Commit the transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit normalization transaction: %w", err)
	}

	logger.Infof(mainCtx, "✅ Successfully normalized %d foreign key references across all tables", totalUpdated)
	return nil
}

func removeEdgeCaseEntries(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	sqlDeleteQueryTemplate := `DELETE FROM %s WHERE %s IN ('%s')`

	dataToRemove := map[string]interface{}{
		"universities": map[string]interface{}{
			"key": "institution",
			"entries": []string{
				// The reason we are removing this row, is because "University Of Masschusetts"
				// is a generic name of a family of universities. https://en.wikipedia.org/wiki/University_of_Massachusetts
				// Specifically, this entry corresponds to six other universities, which is a
				// parent-child mapping we do not support yet. Further, the row for this in universities
				// provides the street address as "South Hawkins Avenue" and city as "Akron"
				// which does not map to any of the six locations for UMass. The currently listed
				// locations are -> 'Amherst,' 'Boston,' 'Dartmouth,' 'Lowell,' 'Worcestor - Medical,'
				// and 'Dartmouth - Law'
				"University Of Massachusetts",
			},
		},
	}

	for tableToRemoveFrom, tableMetadata := range dataToRemove {
		tableMetadataMap := cast.ToStringMap(tableMetadata)
		tableKey := cast.ToString(tableMetadataMap["key"])
		tableEntries := cast.ToStringSlice(tableMetadataMap["entries"])
		sqlFormattedQuery := fmt.Sprintf(sqlDeleteQueryTemplate, tableToRemoveFrom, tableKey, tableEntries)
		if _, err := db.Exec(sqlFormattedQuery); err != nil {
			logger.Errorf(mainCtx, "Failed to execute deleteion query -> '%s'. Error: %v", sqlFormattedQuery, err)
			return fmt.Errorf("failed to execute deletion query for table '%s'. Error: %v", tableToRemoveFrom, err)
		}
	}

	return nil
}

func removeDuplicateEntries(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	sqlDeleteQueryTemplate := `DELETE FROM %s WHERE %s IN (%s)`

	// Define duplicate groups for normalization
	duplicateData := map[string]map[string][]string{
		"professors": {"name": []string{
			"Ronald J. Brachman",
			"Ron Brachman [Tech]",
		}},
		"universities": {"institution": []string{
			// University of California, Berkeley variants
			"U.c. Berkeley",
			"Uc Berkeley",
			"Department Of Mathematics, University Of California, Berkeley",
			"University Of California, Berkeley Department Of Mathematics",
			"University Of California, Berkeley, Department Of Mathematics",
			"Department Of Integrative Biology, Uc Berkeley",
			"The University Of California Berkeley",
			"Univ. of California - Berkeley",
			"University Of California - Berkeley",
			"Univ. Of California, Berkeley, Dept Of Integrative Biology",
			"Univ of California Berkeley",
			"The University Of California, Berkeley",
			"University Of California, Berkeley",
			"University Of California-Berkeley",
			"Univ Of California Berkeley",

			//University Of Illinois Urbana-Champaign variants
			"Univ. of Illinois at Urbana-Champaign",
			"University Of Illinios Urbana-Champaign",
			"University Of Illinois, Urbana-Champaign",
			"University Of Illinois Urbana-Champaign",
			"University Of Illinois At Urbana Champaign",
			"Univ of Illinois at Urbana Champaign",
			"University Of Illinois At Urbana-Champaign",
			"Univ Of Illinois At Urbana Champaign",

			// University of Texas at Austin variants
			"University Of Texas At Austin",
			"University of Texas at Austin",
			"The University Of Texas At Austin",
			"University Of Texas Austin",
			"University Of Texas At Austin Marine Science Institute",
			"The University Of Texas At Austin, Department Of Astronomy",

			// University Of Michigan Ann Arbor variants
			"Regents Of The University Of Michigan Ann Arbor",
			"Regents Of The University Of Michigan - Ann Arbor",

			// University Of California San Diego variants
			"The Regents Of The Univ Of Calif U c San Diego",
			"San Diego State University",
			"University Of California San Diego Scripps Inst Of Oceanography",
			"University Of San Diego",
			"University Of California San Diego (Ucsd)",
			"Univ. of California - San Diego",
			"San Diego State University Foundation",
			"Scripps Institution Of Oceanography Uc San Diego",
			"University Of California San Diego",
			"Univ of California San Diego",
			"University Of California, San Diego",
			"Univ Of California San Diego",

			// University Of Wisconsin Madison variants
			"University Of Wisconsin Madison",
			"University of Wisconsin Madison",
			"University Of Wisconsin, Madison",
			"University Of Wisconsin-Madison / Trout Lake Research Station",
			"University Of Wisconsin - Madison, Dept Of Botany",
			"University Of Wisconsin-Madison",

			// University Of California Los Angeles variants
			"University Of California Los Angeles",
			"University Of California - Los Angeles",
			"University Of California, Los Angeles",
			"Univ. of California - Los Angeles",
			"California State University, Los Angeles",
			"Univ of California Los Angeles",
			"Univ Of California Los Angeles",

			// University Of Marlyand College Park variants
			"University of Maryland College Park",
			"University Of Maryland College Park",
			"University Of Maryland, College Park",

			// Purdue University variants
			"Indiana University-Purdue University At Indianapolis",

			// University Of Massachusetts Amherst
			"University of Massachusetts Amherst",
			"University Of Massachusetts Amherst",
			"University Of Massachusetts - Amherst",

			// University Of California, Irvine
			"University Of California Irvine",
			"Univ. of California - Irvine",
			"University Of California At Irvine",
			"University Of California, Irvine",
			"Univ of California Irvine",
			"Univ Of California Irvine",

			// University Of California, Santa Barbara
			"University Of California Santa Barbara",
			"University Of Califonia, Santa Barbara",
			"Univ. of California - Santa Barbara",
			"Univ of California Santa Barbara",
			"University Of California, Santa Barbara",
			"Univ Of California Santa Barbara",

			// University Of North Carolina Chapel Hill
			"University Of North Carolina Chapel Hill",
			"University Of North Carolina, Chapel Hill",

			// University Of Minnesota Twin Cities
			"University Of Minnesota Twin Cities",
			"University Of Minnesota - Twin Cities",

			// University Of Pennsylvania State University
			"Penn State University, University Park",

			// Carnegie Mellon Variants
			"Carnegie - Mellon University",
			"Carnegie Mellon University",
			"Carnegie Institute",

			// MIT Variants
			"Massachusetts Institute Of Technology Mit",
			"Massachusetts Institute Of Technology",
			"Massachusetts Institute of Technology",

			// University Of Massachusetts
			"University Of Massachusetts",
			"University of Massachusetts Boston",
		},
		},
	}

	// Override map: explicit variant -> canonical name mappings
	universityOverrides := map[string]string{
		// Berkeley
		"U.c. Berkeley": "University of California, Berkeley",
		"Uc Berkeley":   "University of California, Berkeley",
		"Department Of Mathematics, University Of California, Berkeley": "University of California, Berkeley",
		"University Of California, Berkeley Department Of Mathematics":  "University of California, Berkeley",
		"University Of California, Berkeley, Department Of Mathematics": "University of California, Berkeley",
		"Department Of Integrative Biology, Uc Berkeley":                "University of California, Berkeley",
		"The University Of California Berkeley":                         "University of California, Berkeley",
		"Univ. of California - Berkeley":                                "University of California, Berkeley",
		"University Of California - Berkeley":                           "University of California, Berkeley",
		"Univ. Of California, Berkeley, Dept Of Integrative Biology":    "University of California, Berkeley",
		"Univ of California Berkeley":                                   "University of California, Berkeley",
		"The University Of California, Berkeley":                        "University of California, Berkeley",
		"University Of California, Berkeley":                            "University of California, Berkeley",
		"University Of California-Berkeley":                             "University of California, Berkeley",
		"Univ Of California Berkeley":                                   "University of California, Berkeley",

		// UIUC
		"Univ. of Illinois at Urbana-Champaign":      "University of Illinois Urbana-Champaign",
		"University Of Illinios Urbana-Champaign":    "University of Illinois Urbana-Champaign",
		"University Of Illinois, Urbana-Champaign":   "University of Illinois Urbana-Champaign",
		"University Of Illinois Urbana-Champaign":    "University of Illinois Urbana-Champaign",
		"University Of Illinois At Urbana Champaign": "University of Illinois Urbana-Champaign",
		"Univ of Illinois at Urbana Champaign":       "University of Illinois Urbana-Champaign",
		"University Of Illinois At Urbana-Champaign": "University of Illinois Urbana-Champaign",
		"Univ Of Illinois At Urbana Champaign":       "University of Illinois Urbana-Champaign",

		// UT Austin
		"University Of Texas At Austin":                              "University of Texas at Austin",
		"University of Texas at Austin":                              "University of Texas at Austin",
		"The University Of Texas At Austin":                          "University of Texas at Austin",
		"University Of Texas Austin":                                 "University of Texas at Austin",
		"University Of Texas At Austin Marine Science Institute":     "University of Texas at Austin",
		"The University Of Texas At Austin, Department Of Astronomy": "University of Texas at Austin",

		// Michigan
		"Regents Of The University Of Michigan Ann Arbor":   "University of Michigan-Ann Arbor",
		"Regents Of The University Of Michigan - Ann Arbor": "University of Michigan-Ann Arbor",

		// UCSD
		"The Regents Of The Univ Of Calif U c San Diego":                  "University of California, San Diego",
		"San Diego State University":                                      "San Diego State University", // Keep separate
		"University Of California San Diego Scripps Inst Of Oceanography": "University of California, San Diego",
		"University Of San Diego":                                         "University of San Diego", // Keep separate
		"University Of California San Diego (Ucsd)":                       "University of California, San Diego",
		"Univ. of California - San Diego":                                 "University of California, San Diego",
		"San Diego State University Foundation":                           "San Diego State University", // Keep separate
		"Scripps Institution Of Oceanography Uc San Diego":                "University of California, San Diego",
		"University Of California San Diego":                              "University of California, San Diego",
		"Univ of California San Diego":                                    "University of California, San Diego",
		"University Of California, San Diego":                             "University of California, San Diego",
		"Univ Of California San Diego":                                    "University of California, San Diego",

		// Wisconsin-Madison
		"University Of Wisconsin Madison":                               "University of Wisconsin-Madison",
		"University of Wisconsin Madison":                               "University of Wisconsin-Madison",
		"University Of Wisconsin, Madison":                              "University of Wisconsin-Madison",
		"University Of Wisconsin-Madison / Trout Lake Research Station": "University of Wisconsin-Madison",
		"University Of Wisconsin - Madison, Dept Of Botany":             "University of Wisconsin-Madison",
		"University Of Wisconsin-Madison":                               "University of Wisconsin-Madison",

		// UCLA
		"University Of California Los Angeles":     "University of California, Los Angeles",
		"University Of California - Los Angeles":   "University of California, Los Angeles",
		"University Of California, Los Angeles":    "University of California, Los Angeles",
		"Univ. of California - Los Angeles":        "University of California, Los Angeles",
		"California State University, Los Angeles": "California State University, Los Angeles", // Keep separate
		"Univ of California Los Angeles":           "University of California, Los Angeles",
		"Univ Of California Los Angeles":           "University of California, Los Angeles",

		// UMD
		"University of Maryland College Park":  "University of Maryland, College Park",
		"University Of Maryland College Park":  "University of Maryland, College Park",
		"University Of Maryland, College Park": "University of Maryland, College Park",

		// Purdue/IUPUI
		"Indiana University-Purdue University At Indianapolis": "Indiana University-Purdue University Indianapolis",

		// UMass
		"University of Massachusetts Amherst":   "University of Massachusetts - Amherst",
		"University Of Massachusetts Amherst":   "University of Massachusetts - Amherst",
		"University Of Massachusetts - Amherst": "University of Massachusetts - Amherst",
		"University of Massachusetts Boston":    "University of Massachusetts - Boston",
		"University Of Massachusetts Boston":    "University of Massachusetts - Boston",
		"University of Massachusetts Dartmouth": "University of Massachusetts - Dartmouth",
		"University Of Massachusetts Dartmouth": "University of Massachusetts - Dartmouth",
		"University Of Massachusetts Lowell":    "University of Massachusetts - Lowell",
		"University of Massachusetts Lowell":    "University of Massachusetts - Lowell",

		// UC Irvine
		"University Of California Irvine":    "University of California, Irvine",
		"Univ. of California - Irvine":       "University of California, Irvine",
		"University Of California At Irvine": "University of California, Irvine",
		"University Of California, Irvine":   "University of California, Irvine",
		"Univ of California Irvine":          "University of California, Irvine",
		"Univ Of California Irvine":          "University of California, Irvine",

		// UC Santa Barbara
		"University Of California Santa Barbara":  "University of California, Santa Barbara",
		"University Of Califonia, Santa Barbara":  "University of California, Santa Barbara",
		"Univ. of California - Santa Barbara":     "University of California, Santa Barbara",
		"Univ of California Santa Barbara":        "University of California, Santa Barbara",
		"University Of California, Santa Barbara": "University of California, Santa Barbara",
		"Univ Of California Santa Barbara":        "University of California, Santa Barbara",

		// UNC Chapel Hill
		"University Of North Carolina Chapel Hill":  "University of North Carolina at Chapel Hill",
		"University Of North Carolina, Chapel Hill": "University of North Carolina at Chapel Hill",

		// Minnesota
		"University Of Minnesota Twin Cities":   "University of Minnesota-Twin Cities",
		"University Of Minnesota - Twin Cities": "University of Minnesota-Twin Cities",

		// Penn State
		"Penn State University, University Park": "Pennsylvania State University",

		// CMU
		"Carnegie - Mellon University": "Carnegie Mellon University",
		"Carnegie Mellon University":   "Carnegie Mellon University",
		"Carnegie Institute":           "Carnegie Mellon University",

		// MIT
		"Massachusetts Institute Of Technology Mit": "Massachusetts Institute of Technology",
		"Massachusetts Institute Of Technology":     "Massachusetts Institute of Technology",
		"Massachusetts Institute of Technology":     "Massachusetts Institute of Technology",

		// Stanford University
		"Stanford Univeristy": "Stanford University",

		// Georgia University
		"University Of Georgia": "University of Georgia",

		// Georgia Institute of Technology
		"Georgia Institute Of Technology": "Georgia Institute of Technology",

		// George Washington University
		"The George Washington University": "George Washington University",

		// University of Washington
		"University Of Washington":         "University of Washington - Seattle",
		"University Of Washington Tacoma":  "University of Washington - Tacoma",
		"University Of Washington Bothell": "University of Washington - Bothell",

		// Washington University
		"Washington University In St Louis": "Washington University - St Louis",
		"Washington University in St Louis": "Washington University - St Louis",

		// Michigan
		"University Of Michigan - Dearborn":                "University of Michigan - Dearborn",
		"University of Michigan Dearborn":                  "University of Michigan - Dearborn",
		"University Of Michigan Dearborn":                  "University of Michigan - Dearborn",
		"Regents Of The University Of Michigan Dearborn":   "University of Michigan - Dearborn",
		"Regents Of The University Of Michigan - Dearborn": "University of Michigan - Dearborn",
		"The University Of Michigan":                       "University of Michigan - Ann Arbor",
		"University of Michigan":                           "University of Michigan - Ann Arbor",
		"University Of Michigan":                           "University of Michigan - Ann Arbor",
		"Regents Of The University Of Michigan Flint":      "University of Michigan - Flint",
		"Regents Of The University Of Michigan - Flint":    "University of Michigan - Flint",
	}

	// Step 1: Build normalization map for universities and normalize references
	if universityDuplicates, ok := duplicateData["universities"]; ok {
		if institutionVariants, ok := universityDuplicates["institution"]; ok {
			normalizationMap := make(map[string]string)

			// Apply overrides first
			for variant, canonical := range universityOverrides {
				normalizationMap[variant] = canonical
			}

			// Heuristic grouping for anything not in override
			// Group variants by university (currently all in one list, need to split by university)
			// For now, we'll create groups based on common patterns
			groups := make(map[string][]string)

			// Group by university name patterns
			for _, variant := range institutionVariants {
				if _, exists := normalizationMap[variant]; exists {
					continue // Already handled by override
				}

				lower := strings.ToLower(variant)
				var groupKey string

				switch {
				case strings.Contains(lower, "berkeley"):
					groupKey = "berkeley"
				case strings.Contains(lower, "illinois") && strings.Contains(lower, "urbana"):
					groupKey = "illinois_urbana"
				case strings.Contains(lower, "texas") && strings.Contains(lower, "austin"):
					groupKey = "texas_austin"
				case strings.Contains(lower, "michigan") && strings.Contains(lower, "ann arbor"):
					groupKey = "michigan_ann_arbor"
				case strings.Contains(lower, "san diego"):
					groupKey = "san_diego"
				case strings.Contains(lower, "wisconsin") && strings.Contains(lower, "madison"):
					groupKey = "wisconsin_madison"
				case strings.Contains(lower, "los angeles") || strings.Contains(lower, "ucla"):
					groupKey = "ucla"
				case strings.Contains(lower, "maryland") && strings.Contains(lower, "college park"):
					groupKey = "maryland_college_park"
				case strings.Contains(lower, "purdue") || strings.Contains(lower, "indianapolis"):
					groupKey = "purdue_indianapolis"
				case strings.Contains(lower, "massachusetts") && strings.Contains(lower, "amherst"):
					groupKey = "umass_amherst"
				case strings.Contains(lower, "irvine"):
					groupKey = "uci"
				case strings.Contains(lower, "santa barbara"):
					groupKey = "ucsb"
				case strings.Contains(lower, "north carolina") && strings.Contains(lower, "chapel hill"):
					groupKey = "unc_chapel_hill"
				case strings.Contains(lower, "minnesota") && strings.Contains(lower, "twin cities"):
					groupKey = "minnesota_twin_cities"
				case strings.Contains(lower, "penn state"):
					groupKey = "penn_state"
				case strings.Contains(lower, "carnegie"):
					groupKey = "cmu"
				case strings.Contains(lower, "massachusetts institute of technology"):
					groupKey = "mit"
				default:
					continue
				}

				groups[groupKey] = append(groups[groupKey], variant)
			}

			// Build normalization map from heuristic groups (only for non-override variants)
			heuristicMap := buildUniversityNormalizationMap(groups)
			for variant, canonical := range heuristicMap {
				if _, exists := normalizationMap[variant]; !exists {
					normalizationMap[variant] = canonical
				}
			}

			// Log the normalization plan
			logger.Infof(mainCtx, "📋 University normalization plan:")
			for variant, canonical := range normalizationMap {
				logger.Infof(mainCtx, "   '%s' → '%s'", variant, canonical)
			}

			// Normalize all foreign key references
			if err := normalizeUniversityReferences(mainCtx, normalizationMap); err != nil {
				return fmt.Errorf("failed to normalize university references: %w", err)
			}
		}
	}

	// Step 2: Delete duplicate entries
	for table, duplicates := range duplicateData {
		for column, values := range duplicates {
			var deleteQueryBuilder strings.Builder
			for _, val := range values {
				deleteQueryBuilder.WriteString(fmt.Sprintf("'%s', ", strings.ReplaceAll(val, "'", "''")))
			}
			// Remove trailing comma and space
			deleteQuery := strings.TrimSuffix(deleteQueryBuilder.String(), ", ")

			// Construct and execute delete query
			execDeleteQuery := fmt.Sprintf(sqlDeleteQueryTemplate, table, column, deleteQuery)
			result, err := db.Exec(execDeleteQuery)
			if err != nil {
				return fmt.Errorf("failed to remove duplicate entries: %w. Errored query: %v", err, execDeleteQuery)
			}

			rowsAffected, err := result.RowsAffected()
			if err != nil {
				return fmt.Errorf("failed to get rows affected: %w", err)
			}

			logger.Infof(mainCtx, "✅ Removed %d duplicate %s entries from %s", rowsAffected, column, table)
		}
	}

	return nil
}

func removeTagsFromProfessorNames(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	// Update professor names by removing HTML tags
	result, err := db.Exec(`
		UPDATE professors
		SET name = regexp_replace(name, '\s*\[[^]]*\]', '', 'g')
		WHERE name ~ '\[[^]]*\]' 
		AND NOT EXISTS (
			SELECT 1 FROM professors p2
			WHERE p2.name = regexp_replace(professors.name, '\s*\[[^]]*\]', '', 'g')
			AND p2.name <> professors.name
		);
	`)
	if err != nil {
		return fmt.Errorf("failed to update professor names: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	logger.Infof(mainCtx, "✅ Removed Topic Tags from %d professor names", rowsAffected)
	return nil
}

// getParentUniversity maps lab names to their parent universities
func getParentUniversity(labName string) string {
	// Hardcoded mapping of labs to their parent universities
	parentMap := map[string]string{
		// Carnegie Mellon University
		"Carnegie Institution For Science Department Of Embryology": "Carnegie Mellon University",
		"Carnegie Institution For Science":                          "Carnegie Mellon University",
		"Carnegie Learning":                                         "Carnegie Mellon University",
		"Observatories Of The Carnegie Institution For Science":     "Carnegie Mellon University",
		"Carnegie Institution Of Washington":                        "Carnegie Mellon University",

		// MIT
		"Massachusetts Eye And Ear Infirmary":                             "Massachusetts Institute of Technology",
		"Massachusetts General Hospital":                                  "Massachusetts Institute of Technology",
		"Massachusetts Institute Of Technology Department Of Mathematics": "Massachusetts Institute of Technology",
		"Mit Civil And Environmental Engineering":                         "Massachusetts Institute of Technology",
		"Mit Department Of Mathematics":                                   "Massachusetts Institute of Technology",

		// University Of Masachusetts
		"Department Of Linguistics University Of Massachusetts Amherst": "University Of Massachusetts",

		// Stanford University
		"Stanford University Mathematics Department":    "Stanford University",
		"Stanford Nanofabrication Facility Snf":         "Stanford University",
		"Stanford University - Department Of Biology":   "Stanford University",
		"Stanford University Department Of Mathematics": "Stanford University",
		"Stanford University - Biology Department":      "Stanford University",

		// Cornell Tech
		"Cornell Tech": "Cornell University",
		"Joan And Sanford I Weill Medical College Of Cornell University": "Cornell University",

		// University Of Washington
		"University Of Washington Sch Of Marine And Env Affairs":      "University of Washington",
		"University Of Washington Department Of Atmospheric Sciences": "University of Washington",
		"University Of Washington Department Of Mathematics":          "University of Washington",
	}

	// Check if we have a known parent
	if parent, exists := parentMap[labName]; exists {
		return parent
	}

	// Default: return the lab name itself (no known parent)
	return labName
}

func copyOrgsAndStartupsFromUniTable(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return err
	}

	rowsToEntertain := []string{
		"Harvard - Smithsonian Center For Astrophysics",
		"Smithsonian National Museum Of Natural History",
		"Smithsonian Institution",
		"Smith College",
		"RMIT University",
		"Smithsonian Institution Astrophysical Observatory",
		"Mithrilai Corp",
		"Smithsonian Astrophysical Observatory",
		"Massachusetts General Hospital The General Hospital Corp",
		"Nantucket Maria Mitchell Association",
		"Lusk Alexander Dmitri",
		"Scientific Committee On Oceanic Research Scor",
		"Smithsonian Conservation Biology Institute And National Zoo",
		"Coherent Photonics Limited Liability Company",
		"Smithsonian Tropical Research Institute",
		"Mitre Corporation Virginia",
		"Vishwamitra Research Institute",
		"Virolock Technologies Limited Liability Company",
		"Neurx Medical Limited Liability Company",
		"Department Of Invertebrate Zoology Smithsonian Institution",

		// Georgia Tech
		"Georgia Tech Research Corp",
		"Georgia Tech Research Corporation",
		"Georgia Tech Applied Research Corporation",
		"Georgia Biomedical Partnership",
		"Georgia Research Alliance",

		// Cornell
		"Weill Cornell Graduate School Of Medical Sciences",

		// Washington
		"Sharon Washington",
		"Greater Washington Educational Telecommunications Association",
	}

	placeholders := make([]string, len(rowsToEntertain))
	args := make([]interface{}, len(rowsToEntertain))
	for i, name := range rowsToEntertain {
		placeholders[i] = fmt.Sprintf("$%d", i+1)
		args[i] = name
	}

	_, err = db.Exec(fmt.Sprintf(
		"INSERT INTO organizations SELECT * FROM universities WHERE institution IN (%s)", strings.Join(placeholders, ", "),
	), args...)
	if err != nil {
		return fmt.Errorf("failed to copy over rows from the 'universities' table to the 'organizations' table. Error: %v", err)
	}

	return nil
}

func copyLabsFromUniversitiesToLabsTable(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		logger.Errorf(mainCtx, "❌ Cannot get DB: %v", err)
		return fmt.Errorf("cannot get DB: %w", err)
	}

	logger.Infof(mainCtx, "🔎 Searching for labs in universities table...")

	hardcodedLabs := []string{
		// Carnegie Mellon University
		"Carnegie Institution For Science Department Of Embryology",
		"Carnegie Institution For Science",
		"Carnegie Museum Of Natural History",
		"Carnegie Learning",
		"Observatories Of The Carnegie Institution For Science",
		"Carnegie Institution Of Washington",

		// MIT
		"Massachusetts Eye And Ear Infirmary",
		"Massachusetts General Hospital",
		"Massachusetts Institute Of Technology Department Of Mathematics",
		"Mit Civil And Environmental Engineering",
		"Mit Department Of Mathematics",

		// University Of Massachusetts
		"Department Of Linguistics University Of Massachusetts Amherst",

		// Stanford University
		"Stanford University Mathematics Department",
		"Stanford Nanofabrication Facility Snf",
		"Stanford University - Department Of Biology",
		"Stanford University Department Of Mathematics",
		"Stanford University - Biology Department",

		// Cornell
		"Cornell Tech",
		"Joan And Sanford I Weill Medical College Of Cornell University",

		// University of Washington
		"University Of Washington Sch Of Marine And Env Affairs",
		"University Of Washington Department Of Atmospheric Sciences",
		"University Of Washington Department Of Mathematics",
	}
	whereConditions := []string{
		"institution ILIKE '% lab%'",
		"institution ILIKE '% laboratory%'",
		"institution ILIKE '% research center%'",
		"institution ILIKE '% research centre%'",
		"institution ILIKE '% llc%'",
		"institution ILIKE '% inc%'",
		"institution ILIKE '% dept%'",
	}

	// Add exact matches for hardcoded labs
	for _, lab := range hardcodedLabs {
		whereConditions = append(whereConditions, fmt.Sprintf("institution = '%s'", lab))
	}

	dbQuery := fmt.Sprintf(`
		SELECT
			institution,
			COALESCE(street_address, ''),
			COALESCE(city, ''),
			COALESCE(phone, ''),
			COALESCE(zip_code, ''),
			COALESCE(country, ''),
			COALESCE(region, ''),
			COALESCE(countryabbrv, ''),
			COALESCE(homepage, ''),
			latitude,
			longitude
		FROM universities
		WHERE %s
	`, strings.Join(whereConditions, " OR "))

	// Find all labs in universities table
	rows, err := db.Query(dbQuery)
	if err != nil {
		logger.Errorf(mainCtx, "❌ Failed to query labs from universities: %v", err)
		return fmt.Errorf("failed to query labs from universities: %w", err)
	}

	defer rows.Close()

	for rows.Next() {
		tx, err := db.Begin()
		if err != nil {
			logger.Errorf(mainCtx, "❌ Failed to begin transaction: %v", err)
			return fmt.Errorf("failed to begin transaction: %w", err)
		}

		stmt, err := tx.Prepare(`
		INSERT INTO labs (lab, street_address, city, phone, zip_code, country, region, countryabbrv, homepage, latitude, longitude, institution)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
		ON CONFLICT (lab) DO NOTHING;
	`)
		if err != nil {
			logger.Errorf(mainCtx, "❌ Failed to prepare insert statement: %v", err)
			tx.Rollback()
			return fmt.Errorf("failed to prepare insert statement: %w", err)
		}

		var institution, streetAddr, city, phone, zipCode, country, region, countryAbbrv, homepage string
		var latitude, longitude float64
		rowScanErr := rows.Scan(&institution, &streetAddr, &city, &phone, &zipCode, &country, &region, &countryAbbrv, &homepage, &latitude, &longitude)
		if rowScanErr != nil {
			// Handle NULL float64 scan error gracefully for longitude and latitude
			if strings.Contains(rowScanErr.Error(), "converting NULL to float64 is unsupported") {
				// TOOD: This is a a longer effort and affects 12 rows only. We don't have lat,long for
				// these extra rows for some reason (not universities at all), and ideally, we would
				// like to get the long/lat once, and preserve somewhere in the volume beyond the
				// life of this container, and then the container would pick up these once resolved
				// coorindates, and use them ... or we could just Google Map search once instead of
				// wasting 3 hours to automate something that affects only 2 rows. ¯\_(ツ)_/¯
				continue
			}

			logger.Errorf(mainCtx, "❌ Failed to scan lab row: %v", rowScanErr)
			return fmt.Errorf("failed to scan lab row: %w", rowScanErr)
		}

		_, statementExecErr := stmt.Exec(institution, streetAddr, city, phone, zipCode, country, region, countryAbbrv, homepage, latitude, longitude, getParentUniversity(institution))
		if statementExecErr != nil {
			logger.Errorf(mainCtx, "❌ Failed to insert lab '%s': %v", institution, statementExecErr)
			tx.Rollback()
			return fmt.Errorf("failed to insert lab: %w", statementExecErr)
		}

		logger.Infof(mainCtx, "➕ Inserted lab '%s' into labs table.", institution)

		if _, err := tx.Exec(`DELETE FROM universities WHERE institution = $1`, institution); err != nil {
			logger.Errorf(mainCtx, "❌ Failed to delete lab '%s' from universities: %v", institution, err)
			tx.Rollback()
			return fmt.Errorf("failed to delete lab from universities: %w", err)
		}

		logger.Infof(mainCtx, "🗑️ Deleted lab '%s' from universities table.", institution)

		if err := tx.Commit(); err != nil {
			logger.Errorf(mainCtx, "❌ Failed to commit transaction: %v", err)
			return fmt.Errorf("failed to commit transaction: %w", err)
		}

		stmt.Close()
	}

	return nil
}

func validateAndFormatDbData(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	// We need find all instances in the table universities where the institution name
	// needs to be normalized or formatted properly
	// For example, for "Texas A and M", we should normalize it to "Texas A&M"
	// Or, for "Univ. of California - Berkeley", we should normalize it to "University of California, Berkeley"
	// Or, for "Texas A&M University-San Antonio", we should normalize it to "Texas A&M University - San Antonio"
	rows, err := db.Query(`SELECT institution FROM universities`)
	if err != nil {
		return fmt.Errorf("failed to query universities: %w", err)
	}
	defer rows.Close()

	var institutions []string
	for rows.Next() {
		var inst string
		if err := rows.Scan(&inst); err != nil {
			logger.Warnf(mainCtx, "⚠️ Failed to scan institution: %v", err)
			continue
		}
		institutions = append(institutions, inst)
	}

	var updatedCount int
	for _, inst := range institutions {
		normalized := normalizeInstitutionName(inst)
		if normalized != inst {
			// Check if normalized institution already exists
			var exists bool
			err := db.QueryRow(`SELECT EXISTS(SELECT 1 FROM universities WHERE institution = $1)`, normalized).Scan(&exists)
			if err != nil {
				logger.Warnf(mainCtx, "⚠️ Failed to check existence for '%s': %v", normalized, err)
				continue
			}
			if exists {
				// Delete the current row to avoid unique constraint violation
				_, delErr := db.Exec(`DELETE FROM universities WHERE institution = $1`, inst)
				if delErr != nil {
					logger.Warnf(mainCtx, "⚠️ Failed to delete duplicate institution '%s': %v", inst, delErr)
				} else {
					logger.Warnf(mainCtx, "🗑️ Deleted duplicate institution '%s' (normalized as '%s')", inst, normalized)
				}
				continue
			}
			_, err = db.Exec(`UPDATE universities SET institution = $1 WHERE institution = $2`, normalized, inst)
			if err != nil {
				logger.Warnf(mainCtx, "⚠️ Failed to update institution '%s' to '%s': %v", inst, normalized, err)
				continue
			}
			updatedCount++
			logger.Infof(mainCtx, "🔄 Updated institution '%s' to '%s'.", inst, normalized)
		}
	}

	logger.Infof(mainCtx, "✅ Validated and formatted %d institution names in universities table.", updatedCount)
	return nil
}

func markPipelineAsCompleted(mainCtx *colly.Context, step string, status string) {
	db, err := GetDB()
	if err != nil {
		logger.Errorf(mainCtx, "❌ Failed to get DB: %v", err)
		return
	}

	// Check if table exists
	var exists bool
	err = db.QueryRow(`
		SELECT EXISTS (
			SELECT 1
			FROM information_schema.tables 
			WHERE table_schema = 'public' 
			AND table_name = 'pipeline_status'
		)
	`).Scan(&exists)
	if err != nil {
		logger.Errorf(mainCtx, "❌ Failed to check if table exists: %v", err)
		return
	}

	if !exists {
		logger.Warn(mainCtx, "⚠️ Table 'pipeline_status' does not exist, skipping insert/update")
		return
	}

	// Proceed with upsert
	_, err = db.Exec(`
		INSERT INTO pipeline_status (pipeline_name, last_run, status)
		VALUES ($1, NOW(), $2)
		ON CONFLICT (pipeline_name) DO UPDATE SET last_run = NOW(), status = $2;
	`, step, status)
	if err != nil {
		logger.Errorf(mainCtx, "❌ Failed to mark pipeline step '%s' as completed: %v", step, err)
		return
	}

	logger.Infof(mainCtx, "✅ Marked pipeline step '%s' as '%s'", step, status)
}

func GetPipelineStatus(mainCtx *colly.Context, step string) string {
	db, err := GetDB()
	if err != nil {
		return ""
	}

	var status string
	err = db.QueryRow(`
		SELECT status
		FROM pipeline_status
		WHERE pipeline_name = $1;
	`, step).Scan(&status)
	if err != nil {
		if err == sql.ErrNoRows {
			return ""
		}

		logger.Errorf(mainCtx, "❌ Failed to check pipeline step '%s' status: %v", step, err)
		return ""
	}

	return status
}

func executeWorkflows(mainCtx *colly.Context) {
	steps := []struct {
		name string
		fn   func(*colly.Context) error
	}{
		{"Download Pre-Req CSVs", downloadCSVs},
		{"Download NSF Data", downloadNSFData},
		{"Download IPEDS Data", downloadIPEDSData},
		{"Populate From CSVs", populatePostgresFromCSVs},
		{"Remove Tags From Professor Names", removeTagsFromProfessorNames},
		{"Populate From NSF JSONs", populatePostgresFromNsfJsons},
		{"Populate From Script Caches", populatePostgresFromScriptCaches},
		{"Populate Homepages Against Universities", populateHomepagesAgainstUniversities},
		{"Populate From IPEDS' CSVs", populatePostgresFromIpedsCSVs},
		{"Clear Final Data States", clearFinalDataStatesInPostgres},
		{"Sync Professors Affiliations to Universities", syncProfessorsAffiliationsToUniversities},
		{"Sync Professor Interests", syncProfessorInterestsToProfessorsAndUniversities},
		{"Remove Edge Case Entries", removeEdgeCaseEntries},
		{"Remove Duplicate Entries", removeDuplicateEntries},
		{"Validate and Format DB Data", validateAndFormatDbData},
		{"Copy Labs from Universities to Labs Table", copyLabsFromUniversitiesToLabsTable},
		// TODO: We need to introduce a new table where we can copy over
		// rows from 'universities' to tables that are specifically for
		// independent institutions like the "Smithsonian Institute" or
		// the "Mithrilai Corp"
		{"Copy Organizations And Startups Over", copyOrgsAndStartupsFromUniTable},
	}

	totalSteps := len(steps)
	successfulSteps := 0

	// Time tracking: last pipeline completion
	var lastRunTime time.Time
	db, err := GetDB()
	if err == nil {
		err = db.QueryRow(`SELECT last_run FROM pipeline_status WHERE pipeline_name = $1`, string(POPULATION_SUCCEEDED_MESSAGE)).Scan(&lastRunTime)
		if err == nil && !lastRunTime.IsZero() {
			logger.Infof(mainCtx, "⏱️ Last pipeline completed at: %s (%.2f hours ago)", lastRunTime.Format(time.RFC3339), time.Since(lastRunTime).Hours())
		}
	}

	if isDataAlreadyPopulated := GetPipelineStatus(mainCtx, string(POPULATION_SUCCEEDED_MESSAGE)); isDataAlreadyPopulated == string(POPULATION_STATUS_SUCCEEDED) {
		logger.Infof(mainCtx, "ℹ️  Postgres population already completed previously, skipping.")
		return
	}

	logger.Infof(mainCtx, "🚀 Starting Postgres population pipeline with %d steps...", totalSteps)
	markPipelineAsCompleted(mainCtx, string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_IN_PROGRESS))

	pipelineStart := time.Now()
	for i, step := range steps {
		stepStart := time.Now()
		logger.Infof(mainCtx, "🔄 Step %d/%d: '%s' - starting...", i+1, totalSteps, step.name)
		if err := step.fn(mainCtx); err != nil {
			logger.Errorf(mainCtx, "❌ Step %d/%d: '%s' - failed: %v", i+1, totalSteps, step.name, err)
			markPipelineAsCompleted(mainCtx, string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_FAILED))
			logger.Infof(mainCtx, "🛑 Pipeline stopped after %d/%d successful steps.", successfulSteps, totalSteps)
			logger.Infof(mainCtx, "⏱️ Pipeline ran for %s before failure.", time.Since(pipelineStart).String())
			return
		}
		stepDuration := time.Since(stepStart)
		successfulSteps++
		logger.Infof(mainCtx, "✅ Step %d/%d: '%s' - succeeded. (%d/%d steps completed) [Step duration: %s]", i+1, totalSteps, step.name, successfulSteps, totalSteps, stepDuration.String())
	}

	totalDuration := time.Since(pipelineStart)
	logger.Infof(mainCtx, "🎉 Postgres population completed successfully. All %d steps succeeded.", totalSteps)
	logger.Infof(mainCtx, "⏱️ Total pipeline duration: %s", totalDuration.String())
	markPipelineAsCompleted(mainCtx, string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_COMPLETED))
	markPipelineAsCompleted(mainCtx, string(POPULATION_SUCCEEDED_MESSAGE), string(POPULATION_STATUS_SUCCEEDED))
}
