package main

import (
	"context"
	"database/sql"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"html"
	"io"
	"maps"
	"os"
	"path"
	"path/filepath"
	"sort"
	"strconv"
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

	// Run in numeric order of the "<n>_" prefix: a plain string sort puts 10_… before 1_….
	migrationNumber := func(name string) int {
		n, err := strconv.Atoi(strings.SplitN(name, "_", 2)[0])
		if err != nil {
			return 1 << 30
		}
		return n
	}
	sort.SliceStable(sqlFiles, func(i, j int) bool { return migrationNumber(sqlFiles[i]) < migrationNumber(sqlFiles[j]) })

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

		// CSRankings stopped publishing some files (geolocation.csv): a fresh server has only the
		// committed backup/ copy, which then serves as the original.
		if _, err := os.Stat(originalPath); os.IsNotExist(err) {
			if _, err := os.Stat(backupPath); err == nil {
				logger.Warnf(mainCtx, "⚠️ %s not downloaded; using the committed copy in backup/", csvName)
				originalPath = backupPath
			}
		}
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

		if tableName == "professors" {
			// Replace the faculty list: people who left CSRankings, or moved, must not keep old rows.
			// Links to them (nsf_investigators.professor) are cleared and rebuilt by the linking steps.
			if _, err := db.Exec(`DELETE FROM professors`); err != nil {
				return fmt.Errorf("failed to clear professors before reload: %w", err)
			}
		}

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
		// IPEDS is supplementary; a failed year must not block the rest of the pipeline
		if err := RunIPEDSIngestion(mainCtx, dataDir, year); err != nil {
			logger.Warnf(mainCtx, "⚠️ Skipping IPEDS ingestion for the year '%d'. Error: %v", year, err)
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

	for year := nsfAwardsEndYear(); year >= NSFAwardsStartYear; year-- {
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
		region, countryabbrv := getRegionAndCountry(db, nsfJsonData.Institute.Country)

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
			nullIfEmpty(region), nullIfEmpty(countryabbrv))
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
			nsfJsonData.AwardInstrumentText, html.UnescapeString(nsfJsonData.AwardTitleText),
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
			// NSF investigators are not CSRankings faculty; the "Link NSF Investigators To
			// Professors" step decides which of them are.
			if pi.NSFId != "" {
				if _, err = db.Exec(`
					INSERT INTO nsf_investigators (nsf_id, full_name, first_name, last_name, middle_initial)
					VALUES ($1, $2, $3, $4, $5)
					ON CONFLICT (nsf_id) DO UPDATE SET full_name = EXCLUDED.full_name,
						first_name = EXCLUDED.first_name, last_name = EXCLUDED.last_name,
						middle_initial = EXCLUDED.middle_initial;
				`, pi.NSFId, pi.Name, pi.FirstName, pi.LastName, pi.MidInit); err != nil {
					logger.Warnf(mainCtx, "⚠️  NSF investigator upsert failed: %v", err)
				}
			}

			if _, err = db.Exec(`
					INSERT INTO award_pi_rel (award_id, investigator_id, pi_role, pi_start_date, pi_end_date, nsf_id, email)
					VALUES ($1, $2, $3, $4, $5, NULLIF($6, ''), NULLIF($7, ''))
					ON CONFLICT (award_id, investigator_id) DO UPDATE SET
						pi_role = EXCLUDED.pi_role,
						pi_start_date = EXCLUDED.pi_start_date,
						pi_end_date = EXCLUDED.pi_end_date,
						nsf_id = EXCLUDED.nsf_id,
						email = EXCLUDED.email;
				`, nsfJsonData.AwdId, pi.Name, pi.Role, pi.StartDate, pi.EndDate, pi.NSFId, pi.EmailAddr); err != nil {
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

// countryLookup maps a country name (as NSF writes it) to its region and ISO alpha-2 code, from the
// countries table loaded in step 4. Loaded once per pipeline run.
var countryLookup struct {
	sync.Once
	byName map[string][2]string
}

// countryNameAliases covers names NSF uses that differ from the countries table.
var countryNameAliases = map[string]string{"Türkiye": "Turkey"}

// getRegionAndCountry returns the region and lower-case alpha-2 code for a country name. NSF leaves
// the country empty for US institutions; an unknown name returns empty strings (stored as NULL)
// rather than guessing "us".
func getRegionAndCountry(db *sql.DB, country string) (string, string) {
	country = strings.TrimSpace(country)
	if country == "" {
		return "northamerica", "us"
	}
	countryLookup.Do(func() {
		countryLookup.byName = map[string][2]string{}
		rows, err := db.Query(`SELECT name, lower(alpha_2), COALESCE(region, ''), COALESCE(sub_region, '') FROM countries
			WHERE name IS NOT NULL AND alpha_2 IS NOT NULL`)
		if err != nil {
			return
		}
		defer rows.Close()
		for rows.Next() {
			var name, code, region, sub string
			if rows.Scan(&name, &code, &region, &sub) != nil {
				continue
			}
			countryLookup.byName[name] = [2]string{regionSlug(region, sub), code}
		}
	})
	if alias, ok := countryNameAliases[country]; ok {
		country = alias
	}
	if rc, ok := countryLookup.byName[country]; ok {
		return rc[0], rc[1]
	}
	return "", ""
}

// regionSlug turns a UN region into the region names used elsewhere in the universities table.
func regionSlug(region, subRegion string) string {
	switch {
	case subRegion == "Northern America":
		return "northamerica"
	case subRegion == "Latin America and the Caribbean":
		return "southamerica"
	default:
		return strings.ToLower(region) // europe, asia, africa, oceania
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

	// Fill a missing region or country code from the countries table (by country name).
	regionCountryAbbrvQueryUpdate := `
	UPDATE universities u
	SET
		region = COALESCE(u.region, CASE
			WHEN c.sub_region = 'Northern America' THEN 'northamerica'
			WHEN c.sub_region = 'Latin America and the Caribbean' THEN 'southamerica'
			ELSE lower(c.region) END),
		countryabbrv = COALESCE(u.countryabbrv, lower(c.alpha_2))
	FROM countries c
	WHERE c.name = CASE WHEN u.country = 'Türkiye' THEN 'Turkey' ELSE u.country END
	  AND (u.region IS NULL OR u.countryabbrv IS NULL);`

	_, err = db.Exec(regionCountryAbbrvQueryUpdate)
	if err != nil {
		return fmt.Errorf("failed to update universities table: %w", err)
	}

	if err := applyCSRankingsCountries(db); err != nil {
		return err
	}

	logger.Infof(mainCtx, "✅ Cleared final data states in Postgres successfully")

	return nil
}

// applyCSRankingsCountries sets region and country code from CSRankings' country-info.csv for every
// row whose name matches one of its institutions (ignoring punctuation and accents). CSRankings is the
// authority for its own institutions; geocoding put some of them in the wrong country
// ("Babeș Bolyai University" in the US while country-info spells it "Babeș-Bolyai University").
func applyCSRankingsCountries(db *sql.DB) error {
	f, err := os.Open(filepath.Join(getRootDirPath(DATA_DIR), COUNTRY_INFO_FILENAME))
	if err != nil {
		return fmt.Errorf("failed to open %s: %w", COUNTRY_INFO_FILENAME, err)
	}
	defer f.Close()
	records, err := csv.NewReader(f).ReadAll()
	if err != nil {
		return fmt.Errorf("failed to read %s: %w", COUNTRY_INFO_FILENAME, err)
	}
	var names, regions, codes []string
	for i, rec := range records {
		if i == 0 || len(rec) < 3 || rec[2] == "" {
			continue
		}
		names, regions, codes = append(names, rec[0]), append(regions, rec[1]), append(codes, strings.ToLower(rec[2]))
	}
	_, err = db.Exec(`
		UPDATE universities u SET region = c.region, countryabbrv = c.code
		FROM (SELECT DISTINCT ON (k) k, region, code FROM (
		        SELECT institution_key(unaccent(n)) k, r region, c code
		        FROM unnest($1::text[], $2::text[], $3::text[]) AS t(n, r, c)) x ORDER BY k) c
		WHERE institution_key(unaccent(u.institution)) = c.k
		  AND u.countryabbrv IS DISTINCT FROM c.code`, pq.Array(names), pq.Array(regions), pq.Array(codes))
	if err != nil {
		return fmt.Errorf("failed to apply CSRankings countries: %w", err)
	}
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

	// Replace the table with this CSV: rows CSRankings dropped (people who left, old affiliations)
	// must go too, which an upsert would keep.
	txSync, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to start sync transaction: %v", err)
	}
	defer txSync.Rollback()
	if _, err := txSync.Exec(`
		DELETE FROM professor_areas;
		INSERT INTO professor_areas (name, affiliation, area, count, adjusted_count, year)
		SELECT DISTINCT ON (name, affiliation, area, year) name, affiliation, area, count, adjusted_count, year
		FROM staging_professor_areas
		ORDER BY name, affiliation, area, year;`); err != nil {
		return fmt.Errorf("failed to load professor_areas: %v", err)
	}
	if err := txSync.Commit(); err != nil {
		return fmt.Errorf("failed to commit professor_areas: %v", err)
	}

	logger.Infof(mainCtx, "✅ Synchronized professor interests successfully from CSV")
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

// executeWorkflows runs the pipeline on server start: from PIPELINE_FROM_STEP when set, else only
// if it hasn't completed before (a failed run resumes at the step that failed).
func executeWorkflows(mainCtx *colly.Context) {
	fromStep := 0
	if v := os.Getenv("PIPELINE_FROM_STEP"); v != "" {
		n, err := strconv.Atoi(v)
		if err != nil || n < 1 || n > len(pipelineSteps()) {
			logger.Errorf(mainCtx, "❌ PIPELINE_FROM_STEP must be between 1 and %d, got '%s'", len(pipelineSteps()), v)
			return
		}
		fromStep = n
	}
	if isDataAlreadyPopulated := GetPipelineStatus(mainCtx, string(POPULATION_SUCCEEDED_MESSAGE)); fromStep == 0 && isDataAlreadyPopulated == string(POPULATION_STATUS_SUCCEEDED) {
		logger.Infof(mainCtx, "ℹ️  Postgres population already completed previously, skipping.")
		return
	}
	runPipeline(mainCtx, fromStep)
}

type pipelineStep struct {
	name string
	fn   func(*colly.Context) error
}

func pipelineSteps() []pipelineStep {
	return []pipelineStep{
		{"Download Pre-Req CSVs", downloadCSVs},
		{"Download NSF Data", downloadNSFData},
		{"Download IPEDS Data", downloadIPEDSData},
		{"Fetch Source Data", fetchBaseSources},
		{"Populate From CSVs", populatePostgresFromCSVs},
		{"Remove Tags From Professor Names", removeTagsFromProfessorNames},
		{"Populate From NSF JSONs", populatePostgresFromNsfJsons},
		{"Populate From Script Caches", populatePostgresFromScriptCaches},
		{"Populate Homepages Against Universities", populateHomepagesAgainstUniversities},
		{"Populate From IPEDS' CSVs", populatePostgresFromIpedsCSVs},
		{"Clear Final Data States", clearFinalDataStatesInPostgres},
		{"Sync Professors Affiliations to Universities", syncProfessorsAffiliationsToUniversities},
		{"Sync Professor Interests", syncProfessorInterestsToProfessorsAndUniversities},
		{"Load OpenAlex Researchers", loadOpenAlexResearchers},
		{"Remove Edge Case Entries", removeEdgeCaseEntries},
		{"Classify Institutions", classifyInstitutions},
		{"Link IPEDS Institutions", linkIpedsInstitutions},
		{"Merge Duplicate Institutions", mergeDuplicateInstitutions},
		{"Link NSF Investigators To Professors", linkInvestigatorsToProfessors},
		{"Load Funder Grants", loadFunderGrants},
		{"Link Funder Grants", linkFunderGrants},
		{"Load DBLP Papers", loadDblpPapers},
		{"Load OpenAlex Researcher Works", loadOpenAlexResearcherWorks},
		{"Link NSF Investigators By DBLP Affiliation", linkNsfByDblpAffiliation},
		{"Load OpenAlex Works", loadOpenAlexWorks},
		{"Build Explorer Tables", buildExplorerTables},
		{"Fetch OpenAlex Data", fetchOpenAlexSources},
		{"Embed Explorer Work", embedExplorerWork},
		{"Embed Grants", embedGrants},
	}
}

// runPipeline runs every step from fromStep (1-based; 0 = resume after the last completed step).
func runPipeline(mainCtx *colly.Context, fromStep int) {
	steps := pipelineSteps()
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

	// fromStep=N forces a rerun of step N and everything after it, treating earlier steps as done.
	// fromStep=0 skips steps already marked completed, so a failed run resumes where it failed.
	if fromStep > 0 {
		logger.Infof(mainCtx, "⏩ Rerunning from step %d '%s'", fromStep, steps[fromStep-1].name)
	}

	logger.Infof(mainCtx, "🚀 Starting Postgres population pipeline with %d steps...", totalSteps)
	markPipelineAsCompleted(mainCtx, string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_IN_PROGRESS))

	pipelineStart := time.Now()
	// PIPELINE_TO_STEP=N stops after step N (to check a change without running the slow steps after it).
	toStep := 0
	if v := os.Getenv("PIPELINE_TO_STEP"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n >= 1 && n <= totalSteps {
			toStep = n
		}
	}

	for i, step := range steps {
		if toStep > 0 && i+1 > toStep {
			logger.Infof(mainCtx, "⏸️  PIPELINE_TO_STEP=%d: stopping before step %d '%s'", toStep, i+1, step.name)
			return
		}
		stepKey := fmt.Sprintf("step_%02d_%s", i+1, step.name)
		alreadyDone := i+1 < fromStep ||
			(fromStep == 0 && GetPipelineStatus(mainCtx, stepKey) == string(PIPELINE_STATUS_COMPLETED))
		if alreadyDone {
			successfulSteps++
			logger.Infof(mainCtx, "⏭️  Step %d/%d: '%s' - already completed, skipping.", i+1, totalSteps, step.name)
			continue
		}

		stepStart := time.Now()
		logger.Infof(mainCtx, "🔄 Step %d/%d: '%s' - starting...", i+1, totalSteps, step.name)
		markPipelineAsCompleted(mainCtx, stepKey, string(PIPELINE_STATUS_IN_PROGRESS))
		if err := step.fn(mainCtx); err != nil {
			logger.Errorf(mainCtx, "❌ Step %d/%d: '%s' - failed: %v", i+1, totalSteps, step.name, err)
			markPipelineAsCompleted(mainCtx, stepKey, string(PIPELINE_STATUS_FAILED))
			markPipelineAsCompleted(mainCtx, string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_FAILED))
			logger.Infof(mainCtx, "🛑 Pipeline stopped after %d/%d successful steps.", successfulSteps, totalSteps)
			logger.Infof(mainCtx, "⏱️ Pipeline ran for %s before failure.", time.Since(pipelineStart).String())
			return
		}
		stepDuration := time.Since(stepStart)
		markPipelineAsCompleted(mainCtx, stepKey, string(PIPELINE_STATUS_COMPLETED))
		successfulSteps++
		logger.Infof(mainCtx, "✅ Step %d/%d: '%s' - succeeded. (%d/%d steps completed) [Step duration: %s]", i+1, totalSteps, step.name, successfulSteps, totalSteps, stepDuration.String())
	}

	totalDuration := time.Since(pipelineStart)
	logger.Infof(mainCtx, "🎉 Postgres population completed successfully. All %d steps succeeded.", totalSteps)
	logger.Infof(mainCtx, "⏱️ Total pipeline duration: %s", totalDuration.String())
	markPipelineAsCompleted(mainCtx, string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_COMPLETED))
	markPipelineAsCompleted(mainCtx, string(POPULATION_SUCCEEDED_MESSAGE), string(POPULATION_STATUS_SUCCEEDED))
}
