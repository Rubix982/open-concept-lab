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
	"golang.org/x/text/cases"
	"golang.org/x/text/language"
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
	ProjectOutcomesReport *struct {
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
	logger.Infof("🚀 Starting NSF JSON population from: %s", internalContainerPath)

	for year := NSFAwardsEndYear; year >= NSFAwardsStartYear; year-- {
		path := filepath.Join(internalContainerPath, fmt.Sprintf("%d", year))
		files, err := os.ReadDir(path)
		if err != nil {
			logger.Errorf("❌ Failed to read directory %s: %v", path, err)
			return err
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
			_, err = db.Exec(universityUpsertQuery, institute.Name, institute.StreetAddress,
				institute.City, institute.PhoneNumber, institute.ZipCode, institute.Country,
				region, countryabbrv)
			if err != nil {
				logger.Warnf("⚠️  University upsert failed (%s): %v", institute.Name, err)
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
					INSERT INTO award_pi_rel (award_id, program_officer_id, pi_role, pi_start_date, pi_end_date)
					VALUES ($1, $2, $3, $4, $5)
					ON CONFLICT (award_id, program_officer_id) DO UPDATE SET
						pi_role = EXCLUDED.pi_role,
						pi_start_date = EXCLUDED.pi_start_date,
						pi_end_date = EXCLUDED.pi_end_date;
				`, nsfJsonData.AwdId, programOfficerId, pi.Role, pi.StartDate, pi.EndDate); err != nil {
					logger.Warnf("⚠️  Award-PI relationship upsert failed: %v", err)
				}
			}

			logger.Infof("✅ Successfully processed award %s (%d)", nsfJsonData.AwdId, year)
		}
	}

	logger.Infof("🎉 NSF JSON population completed successfully.")
	return nil
}

func ToTitleCase(str string) string {
	return cases.Title(language.English).String(strings.TrimSpace(str))
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
