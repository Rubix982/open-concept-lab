package main

import (
	"database/sql"
	"encoding/csv"
	"encoding/json"
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
	"country-info.csv",
	"geolocation.csv",
	"generated-author-info.csv",
}

type NsfJsonData struct {
	AwdId                                  string  `json:"awd_id"`
	AgcyId                                 string  `json:"agcy_id"`
	TranType                               string  `json:"tran_type"`
	AwardInstrumentText                    string  `json:"awd_istr_txt"`
	AwardTitleText                         string  `json:"awd_titl_txt"`
	FederalCatalogDomesticAssistanceNumber string  `json:"cfda_num"`
	OrgCode                                string  `json:"org_code"`
	PoPhoneNumber                          string  `json:"po_phone"`
	PoEmailNumber                          string  `json:"po_email"`
	PoSignBlockName                        string  `json:"po_sign_block_name"`
	AwardEffectiveDate                     string  `json:"awd_eff_date"`
	AwardExpiryDate                        string  `json:"awd_exp_date"`
	TotalIntendedAwardAmount               float64 `json:"tot_intn_awd_amt"`
	AwardAmount                            float64 `json:"awd_amount"`
	EarliestAmendmentDate                  string  `json:"awd_min_amd_letter_date"`
	MostRecentAmendmentDate                string  `json:"awd_max_amd_letter_date"`
	AwardAbstract                          string  `json:"awd_abstract_narration"`
	AwardARRA                              float64 `json:"awd_arra_amount"`
	DirectorateAbbreviation                string  `json:"dir_abbr"`
	OrganizationDirectorateLongName        string  `json:"org_dir_long_name"`
	DivisionAbbreviation                   string  `json:"div_abbr"`
	OrganizationDivisionLongName           string  `json:"org_div_long_name"`
	AwardingAgencyCode                     string  `json:"awd_agcy_code"`
	FundingAgencyCode                      string  `json:"fund_agcy_code"`
	PrincipalInvestigators                 []struct {
		Role       string `json:"pi_role"`
		FirstName  string `json:"pi_first_name"`
		LastName   string `json:"pi_last_name"`
		MiddleName string `json:"pi_mid_init"`
		NameSuffix string `json:"pi_sufx_name"`
		EmailAddr  string `json:"pi_email_addr"`
		NSFId      string `json:"nsf_id"`
		StartDate  string `json:"pi_start_date"`
		EndDate    string `json:"pi_end_date"`
	} `json:"pi"`
	Institute struct {
		Name                       string `json:"inst_name"`
		StreetAddress              string `json:"inst_street_address"`
		StreetAddressV2            string `json:"inst_street_address_2"`
		City                       string `json:"inst_city_name"`
		StateCode                  string `json:"inst_state_code"`
		StateName                  string `json:"inst_state_name"`
		PhoneNumber                string `json:"inst_phone_num"`
		ZipCode                    string `json:"inst_zip_code"`
		Country                    string `json:"inst_country_name"`
		CongressionalDistrictCode  string `json:"cong_dist_code"`
		StateCongressionalDistrict string `json:"st_cong_dist_code"`
		LegalBusinessName          string `json:"org_lgl_bus_name"`
		ParentUEI                  string `json:"org_prnt_uei_num"`
		InstitutionUEI             string `json:"org_uei_num"`
	} `json:"inst"`
	PerformingInsitute struct {
		InstituteName              string `json:"perf_inst_name"`
		StreetAddr                 string `json:"perf_str_addr"`
		CityName                   string `json:"perf_city_name"`
		StateCode                  string `json:"perf_st_code"`
		StateName                  string `json:"perf_st_name"`
		ZipCode                    string `json:"perf_zip_code"`
		CountryCode                string `json:"perf_ctry_code"`
		CongressionalDistrictCode  string `json:"perf_cong_dist"`
		StateCongressionalDistrict string `json:"perf_st_cong_dist"`
		CountryName                string `json:"perf_ctry_name"`
		CountryFlag                string `json:"perf_ctry_flag"`
	} `json:"perf_inst"`
	ProgramElements []struct {
		ProgramElementCode string `json:"pgm_ele_code"`
		ProgramElementName string `json:"pgm_ele_name"`
	} `json:"pgm_ele"`
	ProgramReference []struct {
		ProgramReferenceCode string `json:"pgm_ref_code"`
		ProgramReferenceName string `json:"pgm_ref_name"`
	} `json:"pgm_ref"`
	ApplicationFunding []struct {
		ApplicationCode     string `json:"app_code"`
		ApplicationName     string `json:"app_name"`
		ApplicationSymbolId string `json:"app_symb_id"`
		FundingCode         string `json:"fund_code"`
		FundingName         string `json:"fund_name"`
		FundingSymbolId     string `json:"fund_symb_id"`
	} `json:"app_fund"`
	FundingObligations []struct {
		FiscalYear      int     `json:"fund_oblg_fiscal_yr"`
		AmountObligated float64 `json:"fund_oblg_amt"`
	} `json:"oblg_fy"`
	ProjectOutcomesReport struct {
		HtmlContent string `json:"por_cntn"`
		RawText     string `json:"por_txt_cntn"`
	} `json:"por"`
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
	   			longitude = EXCLUDED.longitude;`, row[0], row[1], row[2]); err != nil {
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

	internalContainerPath := "/app/data/nsfdata"

	// We will iterate over the years in the reverse order while populating the DB
	for year := NSFAwardsEndYear; year >= NSFAwardsStartYear; year-- {
		path := filepath.Join(internalContainerPath, fmt.Sprintf("%d", year))
		files, err := os.ReadDir(path)
		if err != nil {
			logger.Errorf("❌ Failed to read directory: %v", err)
			return err
		}

		var nsfJsonData NsfJsonData
		for _, file := range files {
			// All are files, all are JSONs
			// read the file, and parse as JSON (map[string]interface{})
			rawBytes, err := os.ReadFile(filepath.Join(path, file.Name()))
			if err != nil {
				logger.Errorf("❌ Failed to read file: %v", err)
				continue
			}

			if err := json.Unmarshal(rawBytes, &nsfJsonData); err != nil {
				logger.Errorf("❌ Failed to parse JSON: %v", err)
				continue
			}

		}
	}

	return nil
}

func cleanHeaders(
	tableName string,
	headers []string,
) []string {
	if tableName == "professors" {
		for i, h := range headers {
			if h == "scholarid" {
				headers[i] = "scholar_id"
			}
		}
	}

	return headers
}
