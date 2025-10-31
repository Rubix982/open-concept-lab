package main

import (
	"database/sql"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"maps"
	"os"
	"path"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	_ "github.com/lib/pq"
	"github.com/lithammer/fuzzysearch/fuzzy"
	"golang.org/x/text/cases"
	"golang.org/x/text/language"
)

const (
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
	"country-info.csv",
	"geolocation.csv",
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

func populatePostgresFromCSVs() error {
	db, err := getPostgresConnection()
	if err != nil {
		logger.Fatalf("❌ Failed to connect to DB: %v", err)
		return err
	}

	defer db.Close()

	// Process each CSV from schemaMap
	for _, csvName := range backwardsCompatibleSchemaMap {
		originalTableName := strings.Split(csvName, ".")[0]
		originalTableName = strings.ReplaceAll(originalTableName, "-", "_")
		tableName := getAlternateTableName(originalTableName)

		originalPath := filepath.Join(getRootDirPath(DATA_DIR), csvName)
		backupPath := filepath.Join(getRootDirPath(BACKUP_DIR), csvName)
		primaryKey := primaryKeyAgainstTable[tableName]

		logger.Infof("📁 Processing CSV: '%s' using primary key: '%s' with table name: '%s'",
			csvName, primaryKey, tableName)

		original, headers, err := readCSVAsMap(originalPath, primaryKey)
		if err != nil {
			logger.Errorf("❌ Failed to read original CSV: %v", err)
			return err
		}
		headers = cleanHeaders(tableName, headers)
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
		} else if err := insertIntoPostgres(db, tableName, headers, merged); err != nil {
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

func populatePostgresFromNsfJsons() error {
	db, err := getPostgresConnection()
	if err != nil {
		logger.Fatalf("❌ Failed to connect to DB: %v", err)
		return err
	}

	defer db.Close()

	internalContainerPath := path.Join(getRootDirPath(DATA_DIR), NSF_DATA_DIR)
	logger.Infof("🚀 Starting NSF JSON population from: %s", internalContainerPath)

	var wg sync.WaitGroup

	for year := NSFAwardsEndYear; year >= NSFAwardsStartYear; year-- {
		wg.Add(1)

		go func(year int) {
			defer wg.Done()
			processNsfAwardPerYear(internalContainerPath, year, db)
		}(year)
	}

	wg.Wait()

	logger.Infof("🎉 NSF JSON population completed successfully.")
	return nil
}

func processNsfAwardPerYear(internalContainerPath string, year int, db *sql.DB) {
	path := filepath.Join(internalContainerPath, fmt.Sprintf("%d", year))
	files, err := os.ReadDir(path)
	if err != nil {
		logger.Errorf("❌ Failed to read directory %s: %v", path, err)
		return
	}

	logger.Infof("📂 Processing %d JSON files for year %d", len(files), year)
	var nsfJsonData NsfJsonData

	for _, file := range files {
		filePath := filepath.Join(path, file.Name())
		rawBytes, err := os.ReadFile(filePath)
		if err != nil {
			logger.Warnf("⚠️  Skipping file (read error): %s (%v)", filePath, err)
			continue
		}

		if err := json.Unmarshal(rawBytes, &nsfJsonData); err != nil {
			logger.Warnf("⚠️  Skipping file (parse error): %s (%v)", filePath, err)
			continue
		}

		logger.Debugf("➡️  Processing award: %s", nsfJsonData.AwdId)
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
			logger.Warnf("⚠️  University upsert failed (%s, normalized '%s'): %v", originalInstName, institute.Name, err)
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
			logger.Warnf("⚠️  Directorate/division upsert failed: %v", err)
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
			logger.Warnf("⚠️  Program officer upsert failed: %v", err)
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
			logger.Warnf("⚠️  Award upsert failed (%s): %v", nsfJsonData.AwdId, err)
			continue
		}

		for _, pe := range nsfJsonData.ProgramElements {
			if _, err = db.Exec(`
					INSERT INTO program_element (award_id, code, name)
					VALUES ($1, $2, $3)
					ON CONFLICT (award_id, code) DO UPDATE SET name = EXCLUDED.name;
				`, nsfJsonData.AwdId, pe.ProgramElementCode, pe.ProgramElementName); err != nil {
				logger.Warnf("⚠️  Program element upsert failed: %v", err)
			}
		}

		for _, pr := range nsfJsonData.ProgramReference {
			if _, err = db.Exec(`
					INSERT INTO program_reference (award_id, code, name)
					VALUES ($1, $2, $3)
					ON CONFLICT (award_id, code) DO UPDATE SET name = EXCLUDED.name;
				`, nsfJsonData.AwdId, pr.ProgramReferenceCode, pr.ProgramReferenceName); err != nil {
				logger.Warnf("⚠️  Program reference upsert failed: %v", err)
			}
		}

		for _, af := range nsfJsonData.ApplicationFunding {
			if _, err = db.Exec(`
					INSERT INTO application_funding (award_id, code, name, symbol_id, funding_code, funding_name, funding_symbol_id)
					VALUES ($1, $2, $3, $4, $5, $6, $7)
					ON CONFLICT (award_id, code) DO UPDATE SET name = EXCLUDED.name, symbol_id = EXCLUDED.symbol_id;
				`, nsfJsonData.AwdId, af.ApplicationCode, af.ApplicationName, af.ApplicationSymbolId, af.FundingCode, af.FundingName, af.FundingSymbolId); err != nil {
				logger.Warnf("⚠️  Application funding upsert failed: %v", err)
			}
		}

		for _, fy := range nsfJsonData.FundingObligations {
			if _, err = db.Exec(`
					INSERT INTO fiscal_year_funding (award_id, fiscal_year, funding_amount)
					VALUES ($1, $2, $3)
					ON CONFLICT (award_id, fiscal_year) DO UPDATE SET funding_amount = EXCLUDED.funding_amount;
				`, nsfJsonData.AwdId, fy.FiscalYear, fy.AmountObligated); err != nil {
				logger.Warnf("⚠️  Fiscal year funding upsert failed: %v", err)
			}
		}

		for _, pi := range nsfJsonData.PrincipalInvestigators {
			if _, err = db.Exec(`
					INSERT INTO professors (name, affiliation, nsf_id)
					VALUES ($1, $2, $3)
					ON CONFLICT (name) DO UPDATE SET nsf_id = EXCLUDED.nsf_id;
				`, pi.Name, normalizeInstitutionName(nsfJsonData.PerformingInsitute.InstituteName), pi.NSFId); err != nil {
				logger.Warnf("⚠️  Professor upsert failed: %v", err)
			}

			if _, err = db.Exec(`
					INSERT INTO award_pi_rel (award_id, investigator_id, pi_role, pi_start_date, pi_end_date)
					VALUES ($1, $2, $3, $4, $5)
					ON CONFLICT (award_id, investigator_id) DO UPDATE SET
						pi_role = EXCLUDED.pi_role,
						pi_start_date = EXCLUDED.pi_start_date,
						pi_end_date = EXCLUDED.pi_end_date;
				`, nsfJsonData.AwdId, pi.Name, pi.Role, pi.StartDate, pi.EndDate); err != nil {
				logger.Warnf("⚠️  Award-PI relationship upsert failed: %v", err)
			}
		}

		logger.Infof("✅ Successfully processed award %s (%d)", nsfJsonData.AwdId, year)
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

func populatePostgresFromScriptCaches() error {
	db, err := getPostgresConnection()
	if err != nil {
		logger.Fatalf("❌ Failed to connect to DB: %v", err)
		return err
	}
	defer db.Close()

	internalContainerPath := path.Join(getRootDirPath(SCRIPTS_DIR), GEOCODING_DIR)
	logger.Infof("🚀 Starting script cache population from: %s", internalContainerPath)

	// Paths
	geoCodedCachePath := path.Join(internalContainerPath, "geocoded_cache.csv")
	reverseGeoCodedCachePath := path.Join(internalContainerPath, "reverse_geocoded_cache.csv")

	// 1️⃣ Handle geocoded cache first
	if err := syncCSVToDB(db, geoCodedCachePath); err != nil {
		logger.Errorf("❌ Failed to sync geocoded cache: %v", err)
		return err
	}

	// 2️⃣ Then reverse-geocoded cache
	if err := syncCSVToDB(db, reverseGeoCodedCachePath); err != nil {
		logger.Errorf("❌ Failed to sync reverse geocoded cache: %v", err)
		return err
	}

	logger.Infof("✅ Completed populating script caches into Postgres")
	return nil
}

// syncCSVToDB reads a CSV file and upserts it into the given table
func syncCSVToDB(
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
		logger.Warnf("⚠️ CSV %s is empty, skipping", filePath)
		return nil
	}

	header := records[0]
	logger.Infof("📄 Found %d rows (excluding header) in %s", len(records)-1, filepath.Base(filePath))

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
			logger.Warnf("⚠️ Row %d failed to insert: %v", i+2, err)
			continue
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	logger.Infof("✅ Synced %s into database successfully", filepath.Base(filePath))
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

func clearFinalDataStatesInPostgres() error {
	// Select all rows from the table 'universities' where 'region' or 'countryabbrv' is null
	// Check the 'country' column value, and update the two values appropriately
	db, err := getPostgresConnection()
	if err != nil {
		logger.Fatalf("❌ Failed to connect to DB: %v", err)
		return err
	}

	defer db.Close()

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

	// institutionUpdateQuery := `
	// UPDATE universities
	// SET institution = CASE
	// 	WHEN institution ILIKE 'Univ of %' THEN 'University Of ' || SUBSTRING(institution FROM 9)
	// 	WHEN institution ILIKE 'Univ. of %' THEN 'University Of ' || SUBSTRING(institution FROM 11)
	// 	WHEN institution ILIKE 'Univ Of %' THEN 'University Of ' || SUBSTRING(institution FROM 10)
	// 	WHEN institution ILIKE 'Univ. Of %' THEN 'University Of ' || SUBSTRING(institution FROM 12)
	// 	WHEN institution ILIKE 'Univ %' THEN 'University ' || SUBSTRING(institution FROM 6)
	// 	WHEN institution ILIKE 'Univ. %' THEN 'University ' || SUBSTRING(institution FROM 7)
	// 	ELSE institution
	// END;`

	// _, err = db.Exec(institutionUpdateQuery)
	// if err != nil {
	// 	return fmt.Errorf("failed to update institution names in universities table: %w", err)
	// }

	logger.Infof("✅ Cleared final data states in Postgres successfully")

	return nil
}

func populateHomepagesAgainstUniversities() error {
	db, err := getPostgresConnection()
	if err != nil {
		return fmt.Errorf("❌ Failed to connect to DB: %v", err)
	}
	defer db.Close()

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
			logger.Warnf("⚠️ Failed to update %s: %v", u.institution, err)
		}
	}
	if err := tx.Commit(); err != nil {
		return err
	}

	logger.Infof("✅ Updated %d institutions (%d fuzzy matched, %d skipped)", updated, fuzzyMatched, skipped)
	return nil
}

func syncProfessorsAffiliationsToUniversities() error {
	db, err := getPostgresConnection()
	if err != nil {
		logger.Fatalf("❌ Failed to connect to DB: %v", err)
		return err
	}
	defer db.Close()

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
			logger.Warnf("⚠️ Failed to scan professor row: %v", err)
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
				logger.Warnf("⚠️ No match found for professor '%s' with affiliation '%s'", profName, affiliation)
				// We should insert the affiliation as a new university
				_, insertErr := db.Exec(`INSERT INTO universities (institution) VALUES ($1) ON CONFLICT (institution) DO NOTHING;`, normalizedAffiliation)
				if insertErr != nil {
					logger.Warnf("⚠️ Failed to insert new university for affiliation '%s': %v", normalizedAffiliation, insertErr)
					atomic.AddInt64(&skipped, 1)
					return
				}
				matchedInstitution = normalizedAffiliation
				logger.Infof("➕ Added new university for affiliation '%s'", normalizedAffiliation)
			} else if err != nil {
				logger.Warnf("⚠️ Fuzzy match failed for professor '%s' with affiliation '%s': %v", profName, affiliation, err)
				atomic.AddInt64(&skipped, 1)
				return
			}

			if err != nil {
				logger.Warnf("⚠️ Fuzzy match failed for professor '%s' with affiliation '%s': %v", profName, affiliation, err)
				atomic.AddInt64(&skipped, 1)
				return
			}

			// Update professor's affiliation to the matched institution
			_, err = db.Exec(`UPDATE professors SET affiliation = $1 WHERE name = $2`, matchedInstitution, profName)
			if err != nil {
				logger.Warnf("⚠️ Failed to update professor '%s' affiliation: %v", profName, err)
				atomic.AddInt64(&skipped, 1)
				return
			}

			atomic.AddInt64(&updated, 1)
		}(prof)
	}

	wg.Wait()

	logger.Infof("✅ Synchronized affiliations for %d professors (%d skipped)", updated, skipped)

	return nil
}

func syncProfessorInterestsToProfessorsAndUniversities() error {
	db, err := getPostgresConnection()
	if err != nil {
		logger.Fatalf("❌ Failed to connect to DB: %v", err)
		return err
	}
	defer db.Close()

	db.SetMaxOpenConns(100)
	db.SetMaxIdleConns(50)
	db.SetConnMaxLifetime(time.Minute * 10)

	file, err := os.Open(filepath.Join(getRootDirPath(DATA_DIR), GEN_AUTHOR_FILENAME))
	if err != nil {
		return fmt.Errorf("failed to open CSV: %v", err)
	}
	defer file.Close()

	reader := csv.NewReader(file)
	records, err := reader.ReadAll()
	if err != nil {
		return fmt.Errorf("failed to read CSV: %v", err)
	}

	// Filter header and invalid rows
	var validRows [][]string
	for _, row := range records {
		if len(row) < 6 || strings.TrimSpace(row[0]) == "name" {
			continue
		}
		validRows = append(validRows, row)
	}

	sem := make(chan struct{}, 50) // limit concurrency to 50 goroutines
	var wg sync.WaitGroup
	var updated, skipped int64

	for _, row := range validRows {
		wg.Add(1)
		sem <- struct{}{}

		go func(row []string) {
			defer wg.Done()
			defer func() { <-sem }()

			name := strings.TrimSpace(row[0])
			affiliation := strings.TrimSpace(row[1])
			area := strings.TrimSpace(row[2])
			count := strings.TrimSpace(row[3])
			adjustedCount := strings.TrimSpace(row[4])
			year := strings.TrimSpace(row[5])

			if name == "" || affiliation == "" || area == "" || count == "" || adjustedCount == "" || year == "" {
				logger.Warnf("⚠️ Skipped invalid row: %v", row)
				atomic.AddInt64(&skipped, 1)
				return
			}

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
				logger.Warnf("⚠️ No match found for professor '%s' with affiliation '%s'", name, affiliation)
				atomic.AddInt64(&skipped, 1)
				return
			}
			if err != nil {
				logger.Warnf("⚠️ Fuzzy match failed for professor '%s' with affiliation '%s': %v", name, affiliation, err)
				atomic.AddInt64(&skipped, 1)
				return
			}

			var matchedProfessor string
			err = db.QueryRow(`
				SELECT name
				FROM professors
				WHERE name % $1
				ORDER BY similarity(name, $1) DESC
				LIMIT 1
			`, name).Scan(&matchedProfessor)

			if err == sql.ErrNoRows {
				logger.Warnf("⚠️ No professor found with name '%s'", name)
				// Add the professor if it does not exist so we can to continue below
				_, insertErr := db.Exec(`
					INSERT INTO professors (name, affiliation)
					VALUES ($1, $2)
					ON CONFLICT (name) DO NOTHING;
				`, name, matchedInstitution)
				if insertErr != nil {
					logger.Warnf("⚠️ Failed to insert new professor '%s': %v", name, insertErr)
					atomic.AddInt64(&skipped, 1)
					return
				}
				logger.Infof("➕ Added new professor '%s' with affiliation '%s'", name, matchedInstitution)
				matchedProfessor = name
			} else if err != nil {
				logger.Warnf("⚠️ Failed to find professor '%s': %v", name, err)
				atomic.AddInt64(&skipped, 1)
				return
			}

			_, err = db.Exec(`
				INSERT INTO professor_areas (name, affiliation, area, count, adjusted_count, year)
				VALUES ($1, $2, $3, $4, $5, $6)
				ON CONFLICT (name, affiliation, area, year)
				DO UPDATE SET
					count = EXCLUDED.count,
					adjusted_count = EXCLUDED.adjusted_count;
			`, matchedProfessor, matchedInstitution, area, count, adjustedCount, year)
			if err != nil {
				logger.Warnf("⚠️ Failed to insert into professor_areas for '%s': %v", matchedProfessor, err)
				atomic.AddInt64(&skipped, 1)
				return
			}

			logger.Infof("✅ Synchronized interests for professor '%s' in area '%s'", matchedProfessor, area)
			atomic.AddInt64(&updated, 1)
		}(row)
	}

	wg.Wait()

	logger.Infof("✅ Synchronized professor interests for %d professors (%d skipped)", updated, skipped)
	return nil
}

func removeDuplicateEntries() error {
	db, err := getPostgresConnection()
	if err != nil {
		logger.Fatalf("❌ Failed to connect to DB: %v", err)
		return err
	}
	defer db.Close()

	// Delete duplicate entries based on name and affiliation, keeping the one with the lowest id
	// NOTE: This is a hardcoded fix for specific known duplicates
	result, err := db.Exec(`
		DELETE FROM professors where name IN ('Ronald J. Brachman', 'Ron Brachman [Tech]')
	`)
	if err != nil {
		return fmt.Errorf("failed to remove duplicate entries: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	logger.Infof("✅ Removed %d duplicate professor entries", rowsAffected)
	return nil
}

func removeTagsFromProfessorNames() error {
	db, err := getPostgresConnection()
	if err != nil {
		logger.Fatalf("❌ Failed to connect to DB: %v", err)
		return err
	}
	defer db.Close()

	// Update professor names by removing HTML tags
	result, err := db.Exec(`
		UPDATE professors
		SET name = regexp_replace(name, '\s*\[[^]]*\]', '', 'g')
		WHERE name ~ '\[[^]]*\]';
	`)
	if err != nil {
		return fmt.Errorf("failed to update professor names: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	logger.Infof("✅ Removed Topic Tags from %d professor names", rowsAffected)
	return nil
}

func markPipelineAsCompleted(step string, status string) {
	db, err := getPostgresConnection()
	if err != nil {
		logger.Fatalf("❌ Failed to connect to DB: %v", err)
		return
	}

	defer db.Close()

	_, err = db.Exec(`
		INSERT INTO pipeline_status (pipeline_name, last_run, status)
		VALUES ($1, NOW(), $2)
		ON CONFLICT (pipeline_name) DO UPDATE SET last_run = NOW(), status = $2;
	`, step, status)
	if err != nil {
		logger.Errorf("❌ Failed to mark pipeline step '%s' as completed: %v", step, err)
		return
	}

	logger.Infof("✅ Marked pipeline step '%s' as completed", step)
}

func isPipelineInProgress(step string) bool {
	db, err := getPostgresConnection()
	if err != nil {
		logger.Fatalf("❌ Failed to connect to DB: %v", err)
		return false
	}

	defer db.Close()

	var status string
	err = db.QueryRow(`
		SELECT status
		FROM pipeline_status
		WHERE pipeline_name = $1;
	`, step).Scan(&status)
	if err != nil {
		if err == sql.ErrNoRows {
			return false
		}
		logger.Errorf("❌ Failed to check pipeline step '%s' status: %v", step, err)
		return false
	}

	return status == string(PIPELINE_STATUS_IN_PROGRESS) && status != string(PIPELINE_STATUS_COMPLETED)
}

func populatePostgres() {
	markPipelineAsCompleted(string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_IN_PROGRESS))

	if downloadCsvErr := downloadCSVs(false); downloadCsvErr != nil {
		logger.Errorf("failed to download csvs: %v", downloadCsvErr)
		markPipelineAsCompleted(string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_FAILED))
		return
	}

	if downloadNsfDataErr := downloadNSFData(false); downloadNsfDataErr != nil {
		logger.Errorf("failed to download NSF data: %v", downloadNsfDataErr)
		markPipelineAsCompleted(string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_FAILED))
		return
	}

	if runMigrationsErr := runMigrations(); runMigrationsErr != nil {
		logger.Errorf("failed to execute migrations: %v", runMigrationsErr)
		markPipelineAsCompleted(string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_FAILED))
		return
	}

	if initPostgresErr := populatePostgresFromCSVs(); initPostgresErr != nil {
		logger.Errorf("failed to initialize postgres: %v", initPostgresErr)
		markPipelineAsCompleted(string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_FAILED))
		return
	}

	if initProgressErr := removeDuplicateEntries(); initProgressErr != nil {
		logger.Errorf("failed to initialize progress: %v", initProgressErr)
		markPipelineAsCompleted(string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_FAILED))
		return
	}

	if initProgressErr := removeTagsFromProfessorNames(); initProgressErr != nil {
		logger.Errorf("failed to remove tags from professor names: %v", initProgressErr)
		markPipelineAsCompleted(string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_FAILED))
		return
	}

	if initProgressErr := populatePostgresFromNsfJsons(); initProgressErr != nil {
		logger.Errorf("failed to initialize progress: %v", initProgressErr)
		markPipelineAsCompleted(string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_FAILED))
		return
	}

	if initProgressErr := populatePostgresFromScriptCaches(); initProgressErr != nil {
		logger.Errorf("failed to initialize script caches: %v", initProgressErr)
		markPipelineAsCompleted(string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_FAILED))
		return
	}

	if initProgressErr := populateHomepagesAgainstUniversities(); initProgressErr != nil {
		logger.Errorf("failed to sync professor affiliations: %v", initProgressErr)
		markPipelineAsCompleted(string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_FAILED))
		return
	}

	if initProgressErr := clearFinalDataStatesInPostgres(); initProgressErr != nil {
		logger.Errorf("failed to clear final data states: %v", initProgressErr)
		markPipelineAsCompleted(string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_FAILED))
		return
	}

	if initProgressErr := syncProfessorsAffiliationsToUniversities(); initProgressErr != nil {
		logger.Errorf("failed to sync professor affiliations: %v", initProgressErr)
		markPipelineAsCompleted(string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_FAILED))
		return
	}

	if initProgressErr := syncProfessorInterestsToProfessorsAndUniversities(); initProgressErr != nil {
		logger.Errorf("failed to sync professor interests to professors and universities: %v", initProgressErr)
		markPipelineAsCompleted(string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_FAILED))
		return
	}

	logger.Infof("🎉 Postgres population completed successfully.")
	markPipelineAsCompleted(string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_COMPLETED))
}
