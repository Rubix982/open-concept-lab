package main

import (
	"archive/zip"
	"bytes"
	"database/sql"
	"encoding/csv"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"

	colly "github.com/gocolly/colly/v2"
	_ "github.com/lib/pq"
	"github.com/spf13/cast"
)

const (
	IPEDSBaseURL    = "https://nces.ed.gov/ipeds/datacenter/data"
	IPEDSWaybackURL = "https://web.archive.org/web/20240822183521/https://nces.ed.gov/ipeds/datacenter/data"
	IPEDSDataDir    = "ipeds_data"
	IPEDSCacheDir   = "ipeds_cache"
	IPEDSDictDir    = "ipeds_dict"
	IPEDSColumndir  = "ipeds_columns"
)

type IPEDSFile struct {
	Key       string
	FileCodes []string
}

type IPEDSFetcher struct {
	year       int
	dataDir    string
	cacheDir   string
	client     *http.Client
	mu         sync.Mutex
	downloaded map[string]bool
}

func NewIPEDSFetcher(year int, rootDataDir string) *IPEDSFetcher {
	yearStr := cast.ToString(year)
	dataDir := filepath.Join(rootDataDir, IPEDSDataDir, yearStr)
	cacheDir := filepath.Join(rootDataDir, IPEDSCacheDir, yearStr)
	dictDir := filepath.Join(rootDataDir, IPEDSDictDir, yearStr)
	columnsDir := filepath.Join(rootDataDir, IPEDSColumndir, yearStr)

	os.MkdirAll(dataDir, os.ModePerm)
	os.MkdirAll(cacheDir, os.ModePerm)
	os.MkdirAll(dictDir, os.ModePerm)
	os.MkdirAll(columnsDir, os.ModePerm)

	return &IPEDSFetcher{
		year:       year,
		dataDir:    dataDir,
		cacheDir:   cacheDir,
		client:     &http.Client{Timeout: 60 * time.Second},
		downloaded: make(map[string]bool),
	}
}

func (f *IPEDSFetcher) getFilesToDownload() []IPEDSFile {
	transformedYear := strings.ReplaceAll(cast.ToString(f.year), "0", "2")

	return []IPEDSFile{
		// Core institutional data
		{Key: "institutions", FileCodes: []string{fmt.Sprintf("HD%d", f.year)}},
		{Key: "institutional_characteristics", FileCodes: []string{fmt.Sprintf("IC%d", f.year)}},
		{Key: "institutional_characteristics_ay", FileCodes: []string{fmt.Sprintf("IC%d_AY", f.year)}},
		{Key: "institutional_characteristics_py", FileCodes: []string{fmt.Sprintf("IC%d_PY", f.year)}},
		{Key: "institutional_mission", FileCodes: []string{fmt.Sprintf("IC%dMission", f.year)}},
		{Key: "insitutional_campuses", FileCodes: []string{fmt.Sprintf("IC%d_PCCAMPUSES", f.year)}},

		// Enrollment Data
		{Key: "enrollment_fall", FileCodes: []string{fmt.Sprintf("EF%dA", f.year)}},
		{Key: "enrollment_fall_age", FileCodes: []string{fmt.Sprintf("EF%dB", f.year)}},
		{Key: "enrollment_fall_residence", FileCodes: []string{fmt.Sprintf("EF%dC", f.year)}},
		{Key: "enrollment_fall_distance", FileCodes: []string{fmt.Sprintf("EF%dA_DIST", f.year)}},
		{Key: "enrollment_fall_full", FileCodes: []string{fmt.Sprintf("EF%dD", f.year)}},
		{Key: "enrollment_12month", FileCodes: []string{fmt.Sprintf("EF%d", f.year)}},
		{Key: "enrollment_12month_dist", FileCodes: []string{fmt.Sprintf("EFFY%d_DIST", f.year)}},
		{Key: "enrollment_high_school", FileCodes: []string{fmt.Sprintf("EFFY%d_HS", f.year)}},

		// Completions / Degrees
		{Key: "completions", FileCodes: []string{fmt.Sprintf("C%d_A", f.year)}},

		// Staff
		{Key: "staff_instructional", FileCodes: []string{fmt.Sprintf("S%d_IS", f.year)}},
		{Key: "salaries_instructional", FileCodes: []string{fmt.Sprintf("SAL%d_IS", f.year)}},

		// Finance - try multiple patterns
		{Key: "finance_public", FileCodes: []string{
			fmt.Sprintf("F%s_F2", transformedYear),
			fmt.Sprintf("F%s", transformedYear),
		}},

		// Admissions
		{Key: "admissions", FileCodes: []string{fmt.Sprintf("ADM%d", f.year)}},

		// Graduation rates
		{Key: "graduation_rates", FileCodes: []string{fmt.Sprintf("GR%d", f.year)}},
		{Key: "graduation_rates_pell", FileCodes: []string{fmt.Sprintf("GR%d_PELL_SSL", f.year)}},

		// Financial aid
		{Key: "financial_aid_summary", FileCodes: []string{fmt.Sprintf("SFAV%s", transformedYear)}},

		// Outcome measures
		{Key: "outcome_measures", FileCodes: []string{fmt.Sprintf("OM%d", f.year)}},

		// Libraries
		{Key: "academic_libraries", FileCodes: []string{fmt.Sprintf("AL%d", f.year)}},
	}
}

func (f *IPEDSFetcher) downloadAndExtract(ctx *colly.Context, file IPEDSFile) error {
	// Check if already extracted
	extractDir := filepath.Join(f.dataDir, file.Key)
	if _, err := os.Stat(extractDir); err == nil {
		logger.Infof(ctx, "[✓] %s already exists. Skipping download.\n", file.Key)
		return nil
	}

	logger.Infof(ctx, "[*] Downloading %s...\n", file.Key)

	var lastErr error
	for _, fileCode := range file.FileCodes {
		sources := []string{
			fmt.Sprintf("%s/%s.zip", IPEDSWaybackURL, fileCode),
			fmt.Sprintf("%s/%s.zip", IPEDSBaseURL, fileCode),
		}

		for _, url := range sources {
			logger.Infof(ctx, "    Trying: %s\n", url)

			resp, err := f.client.Get(url)
			if err != nil {
				logger.Infof(ctx, "    ✗ Failed: %v\n", err)
				lastErr = err
				continue
			}

			if resp.StatusCode != http.StatusOK {
				resp.Body.Close()
				logger.Infof(ctx, "    ✗ HTTP %d\n", resp.StatusCode)
				lastErr = fmt.Errorf("HTTP %d", resp.StatusCode)
				continue
			}

			// Read response body
			body, err := io.ReadAll(resp.Body)
			resp.Body.Close()
			if err != nil {
				logger.Infof(ctx, "    ✗ Failed to read body: %v\n", err)
				lastErr = err
				continue
			}

			// Extract zip to directory
			if err := f.extractZipToDir(body, extractDir); err != nil {
				logger.Infof(ctx, "    ✗ Failed to extract: %v\n", err)
				lastErr = err
				continue
			}

			logger.Infof(ctx, "[✓] %s downloaded and extracted to %s\n", file.Key, extractDir)
			return nil
		}
	}

	return fmt.Errorf("all sources failed for %s: %w", file.Key, lastErr)
}

func (f *IPEDSFetcher) extractZipToDir(zipData []byte, extractDir string) error {
	zipReader, err := zip.NewReader(bytes.NewReader(zipData), int64(len(zipData)))
	if err != nil {
		return fmt.Errorf("failed to open zip: %w", err)
	}

	if err := os.MkdirAll(extractDir, os.ModePerm); err != nil {
		return fmt.Errorf("failed to create directory: %w", err)
	}

	for _, file := range zipReader.File {
		// Only extract CSV files
		if !strings.HasSuffix(strings.ToLower(file.Name), ".csv") {
			continue
		}

		rc, err := file.Open()
		if err != nil {
			return fmt.Errorf("failed to open file in zip: %w", err)
		}

		outPath := filepath.Join(extractDir, filepath.Base(file.Name))
		outFile, err := os.Create(outPath)
		if err != nil {
			rc.Close()
			return fmt.Errorf("failed to create output file: %w", err)
		}

		_, err = io.Copy(outFile, rc)
		outFile.Close()
		rc.Close()

		if err != nil {
			return fmt.Errorf("failed to write file: %w", err)
		}
	}

	return nil
}

func (f *IPEDSFetcher) DownloadAll(ctx *colly.Context) error {
	files := f.getFilesToDownload()

	var wg sync.WaitGroup
	errChan := make(chan error, len(files))
	semaphore := make(chan struct{}, 5) // Limit to 5 concurrent downloads

	for _, file := range files {
		wg.Add(1)
		go func(file IPEDSFile) {
			defer wg.Done()

			// Acquire semaphore
			semaphore <- struct{}{}
			defer func() { <-semaphore }()

			if err := f.downloadAndExtract(ctx, file); err != nil {
				logger.Infof(ctx, "[!] Failed to download %s: %v", file.Key, err)
				errChan <- fmt.Errorf("%s: %w", file.Key, err)
			}
		}(file)
	}

	// Wait for all downloads to complete
	wg.Wait()
	close(errChan)

	// Collect errors
	var errors []error
	for err := range errChan {
		errors = append(errors, err)
	}

	if len(errors) > 0 {
		logger.Infof(ctx, "[!] %d files failed to download", len(errors))
		// Return first error
		return errors[0]
	}

	logger.Infof(ctx, "[✓] All IPEDS data downloaded")
	return nil
}

// IngestToDatabase reads all CSV files and ingests them into PostgreSQL
func (f *IPEDSFetcher) IngestToDatabase(ctx *colly.Context, db *sql.DB) error {
	logger.Info(ctx, "[*] Starting database ingestion...")

	ingestFuncs := map[string]func(*sql.DB, string) error{
		"institutions":                     f.ingestInstitutions,
		"enrollment_fall":                  f.ingestEnrollment,
		"staff_instructional":              f.ingestStaff,
		"finance_public":                   f.ingestFinance,
		"completions":                      f.ingestCompletions,
		"admissions":                       f.ingestAdmissions,
		"institutional_characteristics":    f.ingestInstitutionalCharacteristics,
		"institutional_characteristics_ay": f.ingestTuitionFees,
		"graduation_rates":                 f.ingestGraduationRates,
		"graduation_rates_pell":            f.ingestGraduationPell,
		"salaries_instructional":           f.ingestFacultySalaries,
		"financial_aid_summary":            f.ingestFinancialAid,
		"outcome_measures":                 f.ingestOutcomeMeasures,
		"academic_libraries":               f.ingestLibraries,
	}

	for key, ingestFunc := range ingestFuncs {
		extractDir := filepath.Join(f.dataDir, key)
		if _, err := os.Stat(extractDir); os.IsNotExist(err) {
			logger.Infof(ctx, "[!] Skipping %s - directory not found\n", key)
			continue
		}

		logger.Infof(ctx, "[*] Ingesting %s...\n", key)
		if err := ingestFunc(db, extractDir); err != nil {
			logger.Infof(ctx, "[!] Failed to ingest %s: %v\n", key, err)
			continue
		}
		logger.Infof(ctx, "[✓] Ingested %s\n", key)
	}

	logger.Info(ctx, "[✓] Database ingestion complete")
	return nil
}

// Helper to read first CSV in directory
func (f *IPEDSFetcher) readCSVFromDir(dir string) ([][]string, error) {
	files, err := os.ReadDir(dir)
	if err != nil {
		return nil, err
	}

	for _, file := range files {
		if strings.HasSuffix(strings.ToLower(file.Name()), ".csv") {
			csvPath := filepath.Join(dir, file.Name())
			return f.readCSV(csvPath)
		}
	}

	return nil, fmt.Errorf("no CSV file found in %s", dir)
}

func (f *IPEDSFetcher) readCSV(path string) ([][]string, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	reader := csv.NewReader(file)
	return reader.ReadAll()
}

// Ingestion functions
func (f *IPEDSFetcher) ingestInstitutions(db *sql.DB, dir string) error {
	records, err := f.readCSVFromDir(dir)
	if err != nil {
		return err
	}

	if len(records) < 2 {
		return fmt.Errorf("no data rows")
	}

	headers := records[0]
	columnMap := map[string]string{
		"UNITID": "unitid", "INSTNM": "institution_name", "IALIAS": "institution_alias",
		"ADDR": "address", "CITY": "city", "STABBR": "state", "ZIP": "zip",
		"WEBADDR": "website", "SECTOR": "sector", "ICLEVEL": "institutional_level",
		"CONTROL": "control", "HBCU": "historically_black", "HOSPITAL": "has_hospital",
		"MEDICAL": "has_medical_school", "TRIBAL": "tribal_college", "LANDGRNT": "landgrant",
		"CCBASIC": "carnegie_classification", "LOCALE": "locale", "INSTSIZE": "institution_size",
		"CBSA": "metro_area", "COUNTYNM": "county_name", "OBEREG": "geographic_region",
		"LATITUDE": "latitude", "LONGITUD": "longitude", "F1SYSTYP": "system_type",
		"F1SYSNAM": "system_name",
	}

	indices := make(map[string]int)
	for old := range columnMap {
		for i, h := range headers {
			if strings.TrimSpace(h) == old {
				indices[old] = i
				break
			}
		}
	}

	stmt, err := db.Prepare(`
		INSERT INTO ipeds_institutions (
			unitid, institution_name, institution_alias, address, city, state, zip,
			website, sector, institutional_level, control, historically_black,
			has_hospital, has_medical_school, tribal_college, landgrant,
			carnegie_classification, locale, institution_size, metro_area, county_name,
			geographic_region, latitude, longitude, system_type, system_name
		) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24,$25,$26)
		ON CONFLICT (unitid) DO UPDATE SET
			institution_name = EXCLUDED.institution_name,
			state = EXCLUDED.state
	`)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for i := 1; i < len(records); i++ {
		row := records[i]
		getValue := func(col string) interface{} {
			return getValueFromMap(indices, row, col)
		}

		_, err := stmt.Exec(
			getValue("UNITID"), getValue("INSTNM"), getValue("IALIAS"),
			getValue("ADDR"), getValue("CITY"), getValue("STABBR"), getValue("ZIP"),
			getValue("WEBADDR"), getValue("SECTOR"), getValue("ICLEVEL"),
			getValue("CONTROL"), getValue("HBCU"), getValue("HOSPITAL"),
			getValue("MEDICAL"), getValue("TRIBAL"), getValue("LANDGRNT"),
			getValue("CCBASIC"), getValue("LOCALE"), getValue("INSTSIZE"),
			getValue("CBSA"), getValue("COUNTYNM"), getValue("OBEREG"),
			getValue("LATITUDE"), getValue("LONGITUD"), getValue("F1SYSTYP"),
			getValue("F1SYSNAM"),
		)
		if err != nil {
			return fmt.Errorf("row %d: %w", i, err)
		}
	}

	return nil
}

func (f *IPEDSFetcher) ingestEnrollment(db *sql.DB, dir string) error {
	records, err := f.readCSVFromDir(dir)
	if err != nil {
		return err
	}

	if len(records) < 2 {
		return fmt.Errorf("no data rows")
	}

	headers := records[0]
	getIdx := func(col string) int {
		for i, h := range headers {
			if strings.TrimSpace(h) == col {
				return i
			}
		}
		return -1
	}

	unitidIdx := getIdx("UNITID")
	efalevelIdx := getIdx("EFALEVEL")
	eftotltIdx := getIdx("EFTOTLT")
	eftotlmIdx := getIdx("EFTOTLM")
	eftotlwIdx := getIdx("EFTOTLW")

	// Group by unitid
	type EnrollData struct {
		TotalEnrollment    string
		EnrollmentMen      string
		EnrollmentWomen    string
		UndergraduateTotal string
		GraduateTotal      string
	}

	enrollMap := make(map[string]*EnrollData)

	for i := 1; i < len(records); i++ {
		row := records[i]
		if unitidIdx >= len(row) {
			continue
		}

		unitid := strings.TrimSpace(row[unitidIdx])
		efalevel := ""
		if efalevelIdx < len(row) {
			efalevel = strings.TrimSpace(row[efalevelIdx])
		}

		if _, exists := enrollMap[unitid]; !exists {
			enrollMap[unitid] = &EnrollData{}
		}

		data := enrollMap[unitid]

		switch efalevel {
		case "1": // All students
			if eftotltIdx < len(row) {
				data.TotalEnrollment = row[eftotltIdx]
			}
			if eftotlmIdx < len(row) {
				data.EnrollmentMen = row[eftotlmIdx]
			}
			if eftotlwIdx < len(row) {
				data.EnrollmentWomen = row[eftotlwIdx]
			}
		case "2": // Undergraduate
			if eftotltIdx < len(row) {
				data.UndergraduateTotal = row[eftotltIdx]
			}
		case "4": // Graduate
			if eftotltIdx < len(row) {
				data.GraduateTotal = row[eftotltIdx]
			}
		}
	}

	stmt, err := db.Prepare(`
		INSERT INTO ipeds_enrollment (
			unitid, year, total_enrollment, enrollment_men, enrollment_women,
			undergraduate_total, graduate_total
		) VALUES ($1,$2,$3,$4,$5,$6,$7)
		ON CONFLICT (unitid, year) DO UPDATE SET
			total_enrollment = EXCLUDED.total_enrollment
	`)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for unitid, data := range enrollMap {
		_, err := stmt.Exec(
			unitid, f.year,
			nullIfEmpty(data.TotalEnrollment),
			nullIfEmpty(data.EnrollmentMen),
			nullIfEmpty(data.EnrollmentWomen),
			nullIfEmpty(data.UndergraduateTotal),
			nullIfEmpty(data.GraduateTotal),
		)
		if err != nil {
			return err
		}
	}

	return nil
}

func (f *IPEDSFetcher) ingestStaff(db *sql.DB, dir string) error {
	records, err := f.readCSVFromDir(dir)
	if err != nil {
		return err
	}

	if len(records) < 2 {
		return fmt.Errorf("no data rows")
	}

	headers := records[0]
	getIdx := func(col string) int {
		for i, h := range headers {
			if strings.TrimSpace(h) == col {
				return i
			}
		}
		return -1
	}

	unitidIdx := getIdx("UNITID")
	siscatIdx := getIdx("SISCAT")
	facstatIdx := getIdx("FACSTAT")
	arankIdx := getIdx("ARANK")
	hrtotltIdx := getIdx("HRTOTLT")

	type StaffData struct {
		InstructionalTotal string
		Tenured            string
		TenureTrack        string
	}

	staffMap := make(map[string]*StaffData)

	for i := 1; i < len(records); i++ {
		row := records[i]
		if unitidIdx >= len(row) {
			continue
		}

		unitid := strings.TrimSpace(row[unitidIdx])
		siscat := ""
		facstat := ""
		arank := ""

		if siscatIdx < len(row) {
			siscat = strings.TrimSpace(row[siscatIdx])
		}
		if facstatIdx < len(row) {
			facstat = strings.TrimSpace(row[facstatIdx])
		}
		if arankIdx < len(row) {
			arank = strings.TrimSpace(row[arankIdx])
		}

		if _, exists := staffMap[unitid]; !exists {
			staffMap[unitid] = &StaffData{}
		}

		data := staffMap[unitid]

		// SISCAT=100, FACSTAT=10, ARANK=0: Instructional total
		if siscat == "100" && facstat == "10" && arank == "0" {
			if hrtotltIdx < len(row) {
				data.InstructionalTotal = row[hrtotltIdx]
			}
		}

		// Tenured
		if siscat == "200" && facstat == "20" && arank == "0" {
			if hrtotltIdx < len(row) {
				data.Tenured = row[hrtotltIdx]
			}
		}

		// Tenure-track
		if siscat == "300" && facstat == "30" && arank == "0" {
			if hrtotltIdx < len(row) {
				data.TenureTrack = row[hrtotltIdx]
			}
		}
	}

	stmt, err := db.Prepare(`
		INSERT INTO ipeds_staff (
			unitid, year, instructional_staff_total, tenured_faculty, tenure_track_faculty
		) VALUES ($1,$2,$3,$4,$5)
		ON CONFLICT (unitid, year) DO UPDATE SET
			instructional_staff_total = EXCLUDED.instructional_staff_total
	`)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for unitid, data := range staffMap {
		_, err := stmt.Exec(
			unitid, f.year,
			nullIfEmpty(data.InstructionalTotal),
			nullIfEmpty(data.Tenured),
			nullIfEmpty(data.TenureTrack),
		)
		if err != nil {
			return err
		}
	}

	return nil
}

func (f *IPEDSFetcher) ingestFinance(db *sql.DB, dir string) error {
	records, err := f.readCSVFromDir(dir)
	if err != nil {
		return err
	}

	if len(records) < 2 {
		return fmt.Errorf("no data rows")
	}

	headers := records[0]
	getIdx := func(col string) int {
		for i, h := range headers {
			if strings.TrimSpace(h) == col {
				return i
			}
		}
		return -1
	}

	unitidIdx := getIdx("UNITID")
	totalAssetsIdx := getIdx("F2A01")
	totalRevenuesIdx := getIdx("F2C01")
	totalExpensesIdx := getIdx("F2D01")
	researchTotalIdx := getIdx("F2D03")

	stmt, err := db.Prepare(`
		INSERT INTO ipeds_finance (
			unitid, year, total_assets, total_revenues, total_expenses, research_total
		) VALUES ($1,$2,$3,$4,$5,$6)
		ON CONFLICT (unitid, year) DO UPDATE SET
			total_revenues = EXCLUDED.total_revenues
	`)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for i := 1; i < len(records); i++ {
		row := records[i]
		if unitidIdx >= len(row) {
			continue
		}

		_, err := stmt.Exec(
			getValueFromRow(row, unitidIdx),
			f.year,
			getValueFromRow(row, totalAssetsIdx),
			getValueFromRow(row, totalRevenuesIdx),
			getValueFromRow(row, totalExpensesIdx),
			getValueFromRow(row, researchTotalIdx),
		)
		if err != nil {
			return err
		}
	}

	return nil
}

func (f *IPEDSFetcher) ingestCompletions(db *sql.DB, dir string) error {
	records, err := f.readCSVFromDir(dir)
	if err != nil {
		return err
	}

	if len(records) < 2 {
		return fmt.Errorf("no data rows")
	}

	headers := records[0]
	getIdx := func(col string) int {
		for i, h := range headers {
			if strings.TrimSpace(h) == col {
				return i
			}
		}
		return -1
	}

	unitidIdx := getIdx("UNITID")
	awlevelIdx := getIdx("AWLEVEL")

	// Aggregate by unitid
	degreeCount := make(map[string]map[string]int)

	for i := 1; i < len(records); i++ {
		row := records[i]
		if unitidIdx >= len(row) {
			continue
		}

		unitid := strings.TrimSpace(row[unitidIdx])
		awlevel := ""
		if awlevelIdx < len(row) {
			awlevel = strings.TrimSpace(row[awlevelIdx])
		}

		if _, exists := degreeCount[unitid]; !exists {
			degreeCount[unitid] = make(map[string]int)
		}

		degreeCount[unitid][awlevel]++
	}

	stmt, err := db.Prepare(`
		INSERT INTO ipeds_completions (
			unitid, year, total_degrees, associates_degrees, bachelors_degrees,
			masters_degrees, doctoral_degrees
		) VALUES ($1,$2,$3,$4,$5,$6,$7)
		ON CONFLICT (unitid, year) DO UPDATE SET
			total_degrees = EXCLUDED.total_degrees
	`)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for unitid, levels := range degreeCount {
		total := 0
		for _, count := range levels {
			total += count
		}

		associates := levels["3"]
		bachelors := levels["5"]
		masters := levels["7"]
		doctoral := levels["17"] + levels["19"]

		_, err := stmt.Exec(
			unitid, f.year, total, associates, bachelors, masters, doctoral,
		)
		if err != nil {
			return err
		}
	}

	return nil
}

func (f *IPEDSFetcher) ingestAdmissions(db *sql.DB, dir string) error {
	records, err := f.readCSVFromDir(dir)
	if err != nil {
		return err
	}

	if len(records) < 2 {
		return fmt.Errorf("no data rows")
	}

	headers := records[0]
	getIdx := func(col string) int {
		for i, h := range headers {
			if strings.TrimSpace(h) == col {
				return i
			}
		}
		return -1
	}

	unitidIdx := getIdx("UNITID")
	applcnIdx := getIdx("APPLCN")
	admssnIdx := getIdx("ADMSSN")
	enrltIdx := getIdx("ENRLT")

	stmt, err := db.Prepare(`
		INSERT INTO ipeds_admissions (
			unitid, year, applicants, admitted, enrolled, acceptance_rate, yield_rate
		) VALUES ($1,$2,$3,$4,$5,$6,$7)
		ON CONFLICT (unitid, year) DO UPDATE SET
			applicants = EXCLUDED.applicants
	`)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for i := 1; i < len(records); i++ {
		row := records[i]
		if unitidIdx >= len(row) {
			continue
		}

		// Calculate rates
		var acceptanceRate, yieldRate interface{}
		if applcnIdx < len(row) && admssnIdx < len(row) {
			applicants, _ := strconv.ParseFloat(row[applcnIdx], 64)
			admitted, _ := strconv.ParseFloat(row[admssnIdx], 64)
			if applicants > 0 {
				acceptanceRate = (admitted / applicants) * 100
			}
		}
		if admssnIdx < len(row) && enrltIdx < len(row) {
			admitted, _ := strconv.ParseFloat(row[admssnIdx], 64)
			enrolled, _ := strconv.ParseFloat(row[enrltIdx], 64)
			if admitted > 0 {
				yieldRate = (enrolled / admitted) * 100
			}
		}

		_, err := stmt.Exec(
			getValueFromRow(row, unitidIdx), f.year,
			getValueFromRow(row, applcnIdx), getValueFromRow(row, admssnIdx), getValueFromRow(row, enrltIdx),
			acceptanceRate, yieldRate,
		)
		if err != nil {
			return err
		}
	}

	return nil
}

// ingestInstitutionalCharacteristics ingests IC (Institutional Characteristics) data
func (f *IPEDSFetcher) ingestInstitutionalCharacteristics(db *sql.DB, dir string) error {
	records, err := f.readCSVFromDir(dir)
	if err != nil {
		return err
	}

	if len(records) < 2 {
		return fmt.Errorf("no data rows")
	}

	headers := records[0]
	columnMap := map[string]string{
		"UNITID": "unitid", "OPENADMP": "open_admission", "CREDITS1": "credit_life_experience",
		"CREDITS2": "credit_exam", "CREDITS3": "credit_military", "CREDITS4": "credit_online",
		"SLO5": "student_learning_outcomes", "SLO7": "learning_assessment",
		"CALSYS": "calendar_system", "YRSCOLL": "years_college_required",
		"APPLFEEU": "undergrad_application_fee", "APPLFEEG": "grad_application_fee",
		"ROOM": "room_offered", "BOARD": "board_offered",
		"ROOMCAP": "room_capacity", "BOARDCAP": "board_capacity",
		"ROOMAMT": "room_charge", "BOARDAMT": "board_charge",
	}

	indices := make(map[string]int)
	for old := range columnMap {
		for i, h := range headers {
			if strings.TrimSpace(h) == old {
				indices[old] = i
				break
			}
		}
	}

	stmt, err := db.Prepare(`
		INSERT INTO ipeds_institutional_characteristics (
			unitid, open_admission, credit_life_experience, credit_exam,
			credit_military, credit_online, student_learning_outcomes,
			learning_assessment, calendar_system, years_college_required,
			undergrad_application_fee, grad_application_fee, room_offered,
			board_offered, room_capacity, board_capacity, room_charge, board_charge
		) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18)
		ON CONFLICT (unitid) DO UPDATE SET
			open_admission = EXCLUDED.open_admission
	`)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for i := 1; i < len(records); i++ {
		row := records[i]
		getValue := func(col string) interface{} {
			return getValueFromMap(indices, row, col)
		}

		_, err := stmt.Exec(
			getValue("UNITID"), getValue("OPENADMP"), getValue("CREDITS1"),
			getValue("CREDITS2"), getValue("CREDITS3"), getValue("CREDITS4"),
			getValue("SLO5"), getValue("SLO7"), getValue("CALSYS"),
			getValue("YRSCOLL"), getValue("APPLFEEU"), getValue("APPLFEEG"),
			getValue("ROOM"), getValue("BOARD"), getValue("ROOMCAP"),
			getValue("BOARDCAP"), getValue("ROOMAMT"), getValue("BOARDAMT"),
		)
		if err != nil {
			return fmt.Errorf("row %d: %w", i, err)
		}
	}

	return nil
}

// ingestTuitionFees ingests IC_AY (Tuition and Fees) data
func (f *IPEDSFetcher) ingestTuitionFees(db *sql.DB, dir string) error {
	records, err := f.readCSVFromDir(dir)
	if err != nil {
		return err
	}

	if len(records) < 2 {
		return fmt.Errorf("no data rows")
	}

	headers := records[0]
	columnMap := map[string]string{
		"UNITID": "unitid", "TUITION1": "tuition_in_district",
		"TUITION2": "tuition_in_state", "TUITION3": "tuition_out_of_state",
		"FEE1": "fees_in_district", "FEE2": "fees_in_state", "FEE3": "fees_out_of_state",
		"HRCHG1": "per_credit_in_district", "HRCHG2": "per_credit_in_state",
		"HRCHG3": "per_credit_out_of_state", "TUITION5": "grad_tuition_in_state",
		"TUITION6": "grad_tuition_out_of_state", "FEE5": "grad_fees_in_state",
		"FEE6": "grad_fees_out_of_state",
	}

	indices := make(map[string]int)
	for old := range columnMap {
		for i, h := range headers {
			if strings.TrimSpace(h) == old {
				indices[old] = i
				break
			}
		}
	}

	stmt, err := db.Prepare(`
		INSERT INTO ipeds_tuition_fees (
			unitid, year, tuition_in_district, tuition_in_state, tuition_out_of_state,
			fees_in_district, fees_in_state, fees_out_of_state,
			per_credit_in_district, per_credit_in_state, per_credit_out_of_state,
			grad_tuition_in_state, grad_tuition_out_of_state,
			grad_fees_in_state, grad_fees_out_of_state
		) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
		ON CONFLICT (unitid, year) DO UPDATE SET
			tuition_in_state = EXCLUDED.tuition_in_state
	`)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for i := 1; i < len(records); i++ {
		row := records[i]
		getValue := func(col string) interface{} {
			return getValueFromMap(indices, row, col)
		}

		_, err := stmt.Exec(
			getValue("UNITID"), f.year,
			getValue("TUITION1"), getValue("TUITION2"), getValue("TUITION3"),
			getValue("FEE1"), getValue("FEE2"), getValue("FEE3"),
			getValue("HRCHG1"), getValue("HRCHG2"), getValue("HRCHG3"),
			getValue("TUITION5"), getValue("TUITION6"),
			getValue("FEE5"), getValue("FEE6"),
		)
		if err != nil {
			return fmt.Errorf("row %d: %w", i, err)
		}
	}

	return nil
}

// ingestGraduationRates ingests GR (Graduation Rates) data
func (f *IPEDSFetcher) ingestGraduationRates(db *sql.DB, dir string) error {
	records, err := f.readCSVFromDir(dir)
	if err != nil {
		return err
	}

	if len(records) < 2 {
		return fmt.Errorf("no data rows")
	}

	headers := records[0]
	columnMap := map[string]string{
		"UNITID": "unitid", "GRTYPE": "cohort_type", "GRCOHRT": "cohort_size",
		"GRTOTLT": "completers_total", "GRTOTLM": "completers_men",
		"GRTOTLW": "completers_women", "GRRACE15": "completers_nonresident",
		"GRRACE16": "completers_hispanic", "GRRACE17": "completers_american_indian",
		"GRRACE18": "completers_asian", "GRRACE19": "completers_black",
		"GRRACE20": "completers_hawaiian", "GRRACE21": "completers_white",
		"GRRACE22": "completers_two_or_more", "GRRACE23": "completers_unknown",
	}

	indices := make(map[string]int)
	for old := range columnMap {
		for i, h := range headers {
			if strings.TrimSpace(h) == old {
				indices[old] = i
				break
			}
		}
	}

	stmt, err := db.Prepare(`
		INSERT INTO ipeds_graduation_rates (
			unitid, year, cohort_type, cohort_size, completers_total,
			completers_men, completers_women, completers_nonresident,
			completers_hispanic, completers_american_indian, completers_asian,
			completers_black, completers_hawaiian, completers_white,
			completers_two_or_more, completers_unknown
		) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)
		ON CONFLICT (unitid, year, cohort_type) DO UPDATE SET
			completers_total = EXCLUDED.completers_total
	`)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for i := 1; i < len(records); i++ {
		row := records[i]
		getValue := func(col string) interface{} {
			return getValueFromMap(indices, row, col)
		}

		_, err := stmt.Exec(
			getValue("UNITID"), f.year, getValue("GRTYPE"),
			getValue("GRCOHRT"), getValue("GRTOTLT"), getValue("GRTOTLM"),
			getValue("GRTOTLW"), getValue("GRRACE15"), getValue("GRRACE16"),
			getValue("GRRACE17"), getValue("GRRACE18"), getValue("GRRACE19"),
			getValue("GRRACE20"), getValue("GRRACE21"), getValue("GRRACE22"),
			getValue("GRRACE23"),
		)
		if err != nil {
			return fmt.Errorf("row %d: %w", i, err)
		}
	}

	return nil
}

// ingestGraduationPell ingests GR_PELL_SSL (Graduation by Pell/Loan status) data
func (f *IPEDSFetcher) ingestGraduationPell(db *sql.DB, dir string) error {
	records, err := f.readCSVFromDir(dir)
	if err != nil {
		return err
	}

	if len(records) < 2 {
		return fmt.Errorf("no data rows")
	}

	headers := records[0]
	columnMap := map[string]string{
		"UNITID": "unitid", "PGRTYPE": "cohort_type",
		"PGCOHRT": "pell_cohort_size", "PGTOTLT": "pell_completers_total",
		"PGTOTLM": "pell_completers_men", "PGTOTLW": "pell_completers_women",
		"SGCOHRT": "loan_cohort_size", "SGTOTLT": "loan_completers_total",
		"SGTOTLM": "loan_completers_men", "SGTOTLW": "loan_completers_women",
	}

	indices := make(map[string]int)
	for old := range columnMap {
		for i, h := range headers {
			if strings.TrimSpace(h) == old {
				indices[old] = i
				break
			}
		}
	}

	stmt, err := db.Prepare(`
		INSERT INTO ipeds_graduation_pell (
			unitid, year, cohort_type, pell_cohort_size,
			pell_completers_total, pell_completers_men, pell_completers_women,
			loan_cohort_size, loan_completers_total,
			loan_completers_men, loan_completers_women
		) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
		ON CONFLICT (unitid, year, cohort_type) DO UPDATE SET
			pell_completers_total = EXCLUDED.pell_completers_total
	`)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for i := 1; i < len(records); i++ {
		row := records[i]
		getValue := func(col string) interface{} {
			return getValueFromMap(indices, row, col)
		}

		_, err := stmt.Exec(
			getValue("UNITID"), f.year, getValue("PGRTYPE"),
			getValue("PGCOHRT"), getValue("PGTOTLT"), getValue("PGTOTLM"),
			getValue("PGTOTLW"), getValue("SGCOHRT"), getValue("SGTOTLT"),
			getValue("SGTOTLM"), getValue("SGTOTLW"),
		)
		if err != nil {
			return fmt.Errorf("row %d: %w", i, err)
		}
	}

	return nil
}

// ingestFacultySalaries ingests SAL_IS (Faculty Salaries) data
func (f *IPEDSFetcher) ingestFacultySalaries(db *sql.DB, dir string) error {
	records, err := f.readCSVFromDir(dir)
	if err != nil {
		return err
	}

	if len(records) < 2 {
		return fmt.Errorf("no data rows")
	}

	headers := records[0]
	columnMap := map[string]string{
		"UNITID": "unitid", "ARANK": "academic_rank",
		"SALGEND": "gender", "SALTOTL": "faculty_count",
		"SALARY": "average_salary",
	}

	indices := make(map[string]int)
	for old := range columnMap {
		for i, h := range headers {
			if strings.TrimSpace(h) == old {
				indices[old] = i
				break
			}
		}
	}

	stmt, err := db.Prepare(`
		INSERT INTO ipeds_faculty_salaries (
			unitid, year, academic_rank, gender, faculty_count, average_salary
		) VALUES ($1,$2,$3,$4,$5,$6)
		ON CONFLICT (unitid, year, academic_rank, gender) DO UPDATE SET
			average_salary = EXCLUDED.average_salary
	`)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for i := 1; i < len(records); i++ {
		row := records[i]
		getValue := func(col string) interface{} {
			return getValueFromMap(indices, row, col)
		}

		_, err := stmt.Exec(
			getValue("UNITID"), f.year, getValue("ARANK"),
			getValue("SALGEND"), getValue("SALTOTL"), getValue("SALARY"),
		)
		if err != nil {
			return fmt.Errorf("row %d: %w", i, err)
		}
	}

	return nil
}

// ingestFinancialAid ingests SFAV (Student Financial Aid) data
func (f *IPEDSFetcher) ingestFinancialAid(db *sql.DB, dir string) error {
	records, err := f.readCSVFromDir(dir)
	if err != nil {
		return err
	}

	if len(records) < 2 {
		return fmt.Errorf("no data rows")
	}

	headers := records[0]
	columnMap := map[string]string{
		"UNITID": "unitid", "SCUGRAD": "undergrads_total",
		"SCUGFFN": "fulltime_firsttime_total", "SCFA1N": "federal_grant_recipients",
		"SCFA1P": "federal_grant_percent", "SCFA2N": "pell_recipients",
		"SCFA2P": "pell_percent", "SCFA11N": "state_local_grant_recipients",
		"SCFA11P": "state_local_grant_percent", "SCFA12N": "institutional_grant_recipients",
		"SCFA12P": "institutional_grant_percent", "SCFA13N": "loan_recipients",
		"SCFA13P": "loan_percent", "UAGRNTN": "grant_aid_recipients",
		"UAGRNTP": "grant_aid_percent", "UAGRNTA": "average_grant_amount",
		"ANYAIDN": "any_aid_recipients", "ANYAIDP": "any_aid_percent",
	}

	indices := make(map[string]int)
	for old := range columnMap {
		for i, h := range headers {
			if strings.TrimSpace(h) == old {
				indices[old] = i
				break
			}
		}
	}

	stmt, err := db.Prepare(`
		INSERT INTO ipeds_financial_aid (
			unitid, year, undergrads_total, fulltime_firsttime_total,
			federal_grant_recipients, federal_grant_percent, pell_recipients,
			pell_percent, state_local_grant_recipients, state_local_grant_percent,
			institutional_grant_recipients, institutional_grant_percent,
			loan_recipients, loan_percent, grant_aid_recipients,
			grant_aid_percent, average_grant_amount, any_aid_recipients, any_aid_percent
		) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19)
		ON CONFLICT (unitid, year) DO UPDATE SET
			pell_percent = EXCLUDED.pell_percent
	`)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for i := 1; i < len(records); i++ {
		row := records[i]
		getValue := func(col string) interface{} {
			return getValueFromMap(indices, row, col)
		}

		_, err := stmt.Exec(
			getValue("UNITID"), f.year, getValue("SCUGRAD"), getValue("SCUGFFN"),
			getValue("SCFA1N"), getValue("SCFA1P"), getValue("SCFA2N"),
			getValue("SCFA2P"), getValue("SCFA11N"), getValue("SCFA11P"),
			getValue("SCFA12N"), getValue("SCFA12P"), getValue("SCFA13N"),
			getValue("SCFA13P"), getValue("UAGRNTN"), getValue("UAGRNTP"),
			getValue("UAGRNTA"), getValue("ANYAIDN"), getValue("ANYAIDP"),
		)
		if err != nil {
			return fmt.Errorf("row %d: %w", i, err)
		}
	}

	return nil
}

// ingestOutcomeMeasures ingests OM (Outcome Measures) data
func (f *IPEDSFetcher) ingestOutcomeMeasures(db *sql.DB, dir string) error {
	records, err := f.readCSVFromDir(dir)
	if err != nil {
		return err
	}

	if len(records) < 2 {
		return fmt.Errorf("no data rows")
	}

	headers := records[0]
	columnMap := map[string]string{
		"UNITID": "unitid", "OMCHRT": "outcome_cohort_size",
		"OMAWDP8": "completed_8yr_percent", "OMAWDM8": "completed_8yr_men",
		"OMAWDW8": "completed_8yr_women", "OMENRP8": "enrolled_8yr_percent",
		"OMENRM8": "enrolled_8yr_men", "OMENRW8": "enrolled_8yr_women",
		"OMNRTP8": "neither_8yr_percent",
	}

	indices := make(map[string]int)
	for old := range columnMap {
		for i, h := range headers {
			if strings.TrimSpace(h) == old {
				indices[old] = i
				break
			}
		}
	}

	stmt, err := db.Prepare(`
		INSERT INTO ipeds_outcome_measures (
			unitid, year, outcome_cohort_size, completed_8yr_percent,
			completed_8yr_men, completed_8yr_women, enrolled_8yr_percent,
			enrolled_8yr_men, enrolled_8yr_women, neither_8yr_percent
		) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
		ON CONFLICT (unitid, year) DO UPDATE SET
			completed_8yr_percent = EXCLUDED.completed_8yr_percent
	`)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for i := 1; i < len(records); i++ {
		row := records[i]
		getValue := func(col string) interface{} {
			return getValueFromMap(indices, row, col)
		}

		_, err := stmt.Exec(
			getValue("UNITID"), f.year, getValue("OMCHRT"),
			getValue("OMAWDP8"), getValue("OMAWDM8"), getValue("OMAWDW8"),
			getValue("OMENRP8"), getValue("OMENRM8"), getValue("OMENRW8"),
			getValue("OMNRTP8"),
		)
		if err != nil {
			return fmt.Errorf("row %d: %w", i, err)
		}
	}

	return nil
}

// ingestLibraries ingests AL (Academic Libraries) data
func (f *IPEDSFetcher) ingestLibraries(db *sql.DB, dir string) error {
	records, err := f.readCSVFromDir(dir)
	if err != nil {
		return err
	}

	if len(records) < 2 {
		return fmt.Errorf("no data rows")
	}

	headers := records[0]
	columnMap := map[string]string{
		"UNITID": "unitid", "LSTBOOK": "books_physical", "LEBOOKS": "books_electronic",
		"LSERDL": "serials_digital", "LSERPR": "serials_print", "LDBASES": "databases",
		"LVIDEO": "video_materials", "LAUDIO": "audio_materials",
		"LTOTEXP": "total_expenses", "LSTEXP": "staff_expenses",
		"LCOLEXP": "collection_expenses", "LOPEXP": "operations_expenses",
		"LSTFFTE": "librarian_fte", "LIBTOTH": "service_hours_per_year",
	}

	indices := make(map[string]int)
	for old := range columnMap {
		for i, h := range headers {
			if strings.TrimSpace(h) == old {
				indices[old] = i
				break
			}
		}
	}

	stmt, err := db.Prepare(`
		INSERT INTO ipeds_academic_libraries (
			unitid, year, books_physical, books_electronic,
			serials_digital, serials_print, databases, video_materials,
			audio_materials, total_expenses, staff_expenses,
			collection_expenses, operations_expenses, librarian_fte,
			service_hours_per_year
		) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
		ON CONFLICT (unitid, year) DO UPDATE SET
			total_expenses = EXCLUDED.total_expenses
	`)
	if err != nil {
		return err
	}
	defer stmt.Close()

	for i := 1; i < len(records); i++ {
		row := records[i]
		getValue := func(col string) interface{} {
			return getValueFromMap(indices, row, col)
		}

		_, err := stmt.Exec(
			getValue("UNITID"), f.year, getValue("LSTBOOK"), getValue("LEBOOKS"),
			getValue("LSERDL"), getValue("LSERPR"), getValue("LDBASES"),
			getValue("LVIDEO"), getValue("LAUDIO"), getValue("LTOTEXP"),
			getValue("LSTEXP"), getValue("LCOLEXP"), getValue("LOPEXP"),
			getValue("LSTFFTE"), getValue("LIBTOTH"),
		)
		if err != nil {
			return fmt.Errorf("row %d: %w", i, err)
		}
	}

	return nil
}

// Helper function
func nullIfEmpty(s string) interface{} {
	s = strings.TrimSpace(s)
	if s == "" {
		return nil
	}
	return s
}

func getValueFromRow(row []string, idx int) interface{} {
	if idx >= 0 && idx < len(row) {
		return nullIfEmpty(row[idx])
	}
	return nil
}

func getValueFromMap(indices map[string]int, row []string, col string) interface{} {
	if idx, ok := indices[col]; ok && idx < len(row) {
		return nullIfEmpty(row[idx])
	}
	return nil
}

func RunIPEDSIngestion(ctx *colly.Context, rootDataDir string, year int) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	fetcher := NewIPEDSFetcher(year, rootDataDir)
	return fetcher.IngestToDatabase(ctx, db)
}
