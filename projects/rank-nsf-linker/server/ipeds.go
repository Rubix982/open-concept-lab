package main

import (
	"archive/zip"
	"bytes"
	"encoding/csv"
	"fmt"
	"io"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"
)

type IPEDSFetcher struct {
	baseURL    string
	waybackURL string
	year       int
	client     *http.Client
}

func NewIPEDSFetcher(year int) *IPEDSFetcher {
	baseURL := "https://nces.ed.gov/ipeds/datacenter/data"
	waybackURL := fmt.Sprintf("https://web.archive.org/web/20240822183521/%s", baseURL)

	return &IPEDSFetcher{
		baseURL:    baseURL,
		waybackURL: waybackURL,
		year:       year,
		client: &http.Client{
			Timeout: 60 * time.Second,
		},
	}
}

func (f *IPEDSFetcher) downloadAndExtractCSV(fileCode string) ([][]string, error) {
	sources := []string{
		fmt.Sprintf("%s/%s.zip", f.waybackURL, fileCode),
	}

	for _, url := range sources {
		fmt.Printf("Downloading from %s...\n", url)

		resp, err := f.client.Get(url)
		if err != nil {
			fmt.Printf("✗ Failed: %v\n", err)
			continue
		}
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK {
			fmt.Printf("✗ HTTP %d\n", resp.StatusCode)
			continue
		}

		// Read response body
		body, err := io.ReadAll(resp.Body)
		if err != nil {
			fmt.Printf("✗ Failed to read body: %v\n", err)
			continue
		}

		// Open zip archive
		zipReader, err := zip.NewReader(bytes.NewReader(body), int64(len(body)))
		if err != nil {
			fmt.Printf("✗ Failed to open zip: %v\n", err)
			continue
		}

		// Find CSV file
		var csvFile *zip.File
		for _, file := range zipReader.File {
			if strings.HasSuffix(strings.ToLower(file.Name), ".csv") {
				csvFile = file
				break
			}
		}

		if csvFile == nil {
			fmt.Printf("✗ No CSV found in archive\n")
			continue
		}

		fmt.Printf("  Reading: %s\n", csvFile.Name)

		// Open CSV file
		rc, err := csvFile.Open()
		if err != nil {
			fmt.Printf("✗ Failed to open CSV: %v\n", err)
			continue
		}
		defer rc.Close()

		// Parse CSV
		reader := csv.NewReader(rc)
		records, err := reader.ReadAll()
		if err != nil {
			fmt.Printf("✗ Failed to parse CSV: %v\n", err)
			continue
		}

		fmt.Printf("✓ Loaded %d rows\n", len(records)-1)
		return records, nil
	}

	return nil, fmt.Errorf("all sources failed for %s", fileCode)
}

func (f *IPEDSFetcher) FetchInstitutions() ([][]string, error) {
	fileCode := fmt.Sprintf("HD%d", f.year)
	return f.downloadAndExtractCSV(fileCode)
}

func (f *IPEDSFetcher) FetchEnrollment() ([][]string, error) {
	fileCode := fmt.Sprintf("EF%dA", f.year)
	return f.downloadAndExtractCSV(fileCode)
}

func (f *IPEDSFetcher) FetchStaff() ([][]string, error) {
	fileCode := fmt.Sprintf("S%d_IS", f.year)
	return f.downloadAndExtractCSV(fileCode)
}

func (f *IPEDSFetcher) FetchFinance() ([][]string, error) {
	// Try multiple finance file patterns
	transformedYear := strings.Replace(strconv.Itoa(f.year), "0", "2", -1)
	year, _ := strconv.Atoi(transformedYear)

	fileCodes := []string{
		fmt.Sprintf("F%d_F2", year),
		fmt.Sprintf("F%d_F1A", year),
		fmt.Sprintf("F%d", year),
	}

	for _, code := range fileCodes {
		data, err := f.downloadAndExtractCSV(code)
		if err == nil {
			return data, nil
		}
	}

	return nil, fmt.Errorf("all finance sources failed")
}

func (f *IPEDSFetcher) FetchCompletions() ([][]string, error) {
	fileCode := fmt.Sprintf("C%d_A", f.year)
	return f.downloadAndExtractCSV(fileCode)
}

func (f *IPEDSFetcher) FetchAdmissions() ([][]string, error) {
	fileCode := fmt.Sprintf("ADM%d", f.year)
	return f.downloadAndExtractCSV(fileCode)
}

// CSV writing utilities

func writeCSV(filename string, records [][]string) error {
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	return writer.WriteAll(records)
}

func getColumnIndex(headers []string, columnName string) int {
	for i, header := range headers {
		if strings.TrimSpace(header) == columnName {
			return i
		}
	}
	return -1
}

func extractColumns(records [][]string, columnMap map[string]string) [][]string {
	if len(records) == 0 {
		return nil
	}

	headers := records[0]

	// Build new header
	newHeaders := make([]string, 0, len(columnMap))
	columnIndices := make([]int, 0, len(columnMap))

	for oldName, newName := range columnMap {
		idx := getColumnIndex(headers, oldName)
		if idx >= 0 {
			newHeaders = append(newHeaders, newName)
			columnIndices = append(columnIndices, idx)
		}
	}

	// Extract data
	result := make([][]string, 0, len(records))
	result = append(result, newHeaders)

	for i := 1; i < len(records); i++ {
		row := records[i]
		newRow := make([]string, len(columnIndices))
		for j, idx := range columnIndices {
			if idx < len(row) {
				newRow[j] = row[idx]
			} else {
				newRow[j] = ""
			}
		}
		result = append(result, newRow)
	}

	return result
}

func TransformInstitutions(records [][]string) [][]string {
	columnMap := map[string]string{
		"UNITID":   "unitid",
		"INSTNM":   "institution_name",
		"IALIAS":   "institution_alias",
		"ADDR":     "address",
		"CITY":     "city",
		"STABBR":   "state",
		"ZIP":      "zip",
		"WEBADDR":  "website",
		"SECTOR":   "sector",
		"ICLEVEL":  "institutional_level",
		"CONTROL":  "control",
		"HBCU":     "historically_black",
		"HOSPITAL": "has_hospital",
		"MEDICAL":  "has_medical_school",
		"TRIBAL":   "tribal_college",
		"LANDGRNT": "landgrant",
		"CCBASIC":  "carnegie_classification",
		"LOCALE":   "locale",
		"INSTSIZE": "institution_size",
		"CBSA":     "metro_area",
		"COUNTYNM": "county_name",
		"OBEREG":   "geographic_region",
		"LATITUDE": "latitude",
		"LONGITUD": "longitude",
		"F1SYSTYP": "system_type",
		"F1SYSNAM": "system_name",
	}

	return extractColumns(records, columnMap)
}

func TransformEnrollment(records [][]string, year int) [][]string {
	if len(records) == 0 {
		return nil
	}

	headers := records[0]
	unitidIdx := getColumnIndex(headers, "UNITID")
	efalevelIdx := getColumnIndex(headers, "EFALEVEL")
	eftotltIdx := getColumnIndex(headers, "EFTOTLT")
	eftotlmIdx := getColumnIndex(headers, "EFTOTLM")
	eftotlwIdx := getColumnIndex(headers, "EFTOTLW")
	efaiantIdx := getColumnIndex(headers, "EFAIANT")
	efasiatIdx := getColumnIndex(headers, "EFASIAT")
	efbkaatIdx := getColumnIndex(headers, "EFBKAAT")
	efhisptIdx := getColumnIndex(headers, "EFHISPT")
	efwhittIdx := getColumnIndex(headers, "EFWHITT")
	ef2mortIdx := getColumnIndex(headers, "EF2MORT")
	efnraltIdx := getColumnIndex(headers, "EFNRALT")

	// Group by UNITID and EFALEVEL
	type EnrollmentData struct {
		TotalEnrollment    string
		EnrollmentMen      string
		EnrollmentWomen    string
		UndergraduateTotal string
		GraduateTotal      string
		AmericanIndian     string
		Asian              string
		Black              string
		Hispanic           string
		White              string
		TwoOrMore          string
		NonresidentAlien   string
	}

	enrollmentMap := make(map[string]*EnrollmentData)

	for i := 1; i < len(records); i++ {
		row := records[i]
		if len(row) <= unitidIdx {
			continue
		}

		unitid := row[unitidIdx]
		efalevel := row[efalevelIdx]

		if _, exists := enrollmentMap[unitid]; !exists {
			enrollmentMap[unitid] = &EnrollmentData{}
		}

		data := enrollmentMap[unitid]

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
			if efaiantIdx < len(row) {
				data.AmericanIndian = row[efaiantIdx]
			}
			if efasiatIdx < len(row) {
				data.Asian = row[efasiatIdx]
			}
			if efbkaatIdx < len(row) {
				data.Black = row[efbkaatIdx]
			}
			if efhisptIdx < len(row) {
				data.Hispanic = row[efhisptIdx]
			}
			if efwhittIdx < len(row) {
				data.White = row[efwhittIdx]
			}
			if ef2mortIdx < len(row) {
				data.TwoOrMore = row[ef2mortIdx]
			}
			if efnraltIdx < len(row) {
				data.NonresidentAlien = row[efnraltIdx]
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

	// Build output
	result := [][]string{
		{
			"unitid", "total_enrollment", "enrollment_men", "enrollment_women",
			"undergraduate_total", "graduate_total",
			"american_indian_total", "asian_total", "black_total",
			"hispanic_total", "white_total", "two_or_more_races_total",
			"nonresident_alien_total", "year",
		},
	}

	for unitid, data := range enrollmentMap {
		row := []string{
			unitid,
			data.TotalEnrollment,
			data.EnrollmentMen,
			data.EnrollmentWomen,
			data.UndergraduateTotal,
			data.GraduateTotal,
			data.AmericanIndian,
			data.Asian,
			data.Black,
			data.Hispanic,
			data.White,
			data.TwoOrMore,
			data.NonresidentAlien,
			strconv.Itoa(year),
		}
		result = append(result, row)
	}

	return result
}

func TransformStaff(records [][]string, year int) [][]string {
	if len(records) == 0 {
		return nil
	}

	headers := records[0]
	unitidIdx := getColumnIndex(headers, "UNITID")
	siscatIdx := getColumnIndex(headers, "SISCAT")
	facstatIdx := getColumnIndex(headers, "FACSTAT")
	arankIdx := getColumnIndex(headers, "ARANK")
	hrtotltIdx := getColumnIndex(headers, "HRTOTLT")
	hrtotlmIdx := getColumnIndex(headers, "HRTOTLM")
	hrtotlwIdx := getColumnIndex(headers, "HRTOTLW")
	hraiantIdx := getColumnIndex(headers, "HRAIANT")
	hrasiatIdx := getColumnIndex(headers, "HRASIAT")
	hrbkaatIdx := getColumnIndex(headers, "HRBKAAT")
	hrhisptIdx := getColumnIndex(headers, "HRHISPT")
	hrwhittIdx := getColumnIndex(headers, "HRWHITT")
	hr2mortIdx := getColumnIndex(headers, "HR2MORT")
	hrnraltIdx := getColumnIndex(headers, "HRNRALT")

	type StaffData struct {
		InstructionalTotal  string
		InstructionalMen    string
		InstructionalWomen  string
		Tenured             string
		TenureTrack         string
		NotTenureTrack      string
		Professors          string
		AssociateProfessors string
		AssistantProfessors string
		Instructors         string
		AmericanIndian      string
		Asian               string
		Black               string
		Hispanic            string
		White               string
		TwoOrMore           string
		NonresidentAlien    string
	}

	staffMap := make(map[string]*StaffData)

	for i := 1; i < len(records); i++ {
		row := records[i]
		if len(row) <= unitidIdx {
			continue
		}

		unitid := row[unitidIdx]
		siscat := row[siscatIdx]
		facstat := row[facstatIdx]
		arank := row[arankIdx]

		if _, exists := staffMap[unitid]; !exists {
			staffMap[unitid] = &StaffData{}
		}

		data := staffMap[unitid]

		// SISCAT=100, FACSTAT=10, ARANK=0: Instructional staff total
		if siscat == "100" && facstat == "10" && arank == "0" {
			if hrtotltIdx < len(row) {
				data.InstructionalTotal = row[hrtotltIdx]
			}
			if hrtotlmIdx < len(row) {
				data.InstructionalMen = row[hrtotlmIdx]
			}
			if hrtotlwIdx < len(row) {
				data.InstructionalWomen = row[hrtotlwIdx]
			}
			// Demographics
			if hraiantIdx < len(row) {
				data.AmericanIndian = row[hraiantIdx]
			}
			if hrasiatIdx < len(row) {
				data.Asian = row[hrasiatIdx]
			}
			if hrbkaatIdx < len(row) {
				data.Black = row[hrbkaatIdx]
			}
			if hrhisptIdx < len(row) {
				data.Hispanic = row[hrhisptIdx]
			}
			if hrwhittIdx < len(row) {
				data.White = row[hrwhittIdx]
			}
			if hr2mortIdx < len(row) {
				data.TwoOrMore = row[hr2mortIdx]
			}
			if hrnraltIdx < len(row) {
				data.NonresidentAlien = row[hrnraltIdx]
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

		// Not tenure-track
		if siscat == "400" && facstat == "40" && arank == "0" {
			if hrtotltIdx < len(row) {
				data.NotTenureTrack = row[hrtotltIdx]
			}
		}

		// By rank
		if facstat == "10" {
			if siscat == "101" && arank == "1" && hrtotltIdx < len(row) {
				data.Professors = row[hrtotltIdx]
			}
			if siscat == "102" && arank == "2" && hrtotltIdx < len(row) {
				data.AssociateProfessors = row[hrtotltIdx]
			}
			if siscat == "103" && arank == "3" && hrtotltIdx < len(row) {
				data.AssistantProfessors = row[hrtotltIdx]
			}
			if siscat == "104" && arank == "4" && hrtotltIdx < len(row) {
				data.Instructors = row[hrtotltIdx]
			}
		}
	}

	// Build output
	result := [][]string{
		{
			"unitid", "instructional_staff_total", "instructional_staff_men", "instructional_staff_women",
			"tenured_faculty", "tenure_track_faculty", "not_tenure_track_faculty",
			"professors", "associate_professors", "assistant_professors", "instructors",
			"american_indian_faculty", "asian_faculty", "black_faculty",
			"hispanic_faculty", "white_faculty", "two_or_more_races_faculty",
			"nonresident_alien_faculty", "year",
		},
	}

	for unitid, data := range staffMap {
		row := []string{
			unitid,
			data.InstructionalTotal,
			data.InstructionalMen,
			data.InstructionalWomen,
			data.Tenured,
			data.TenureTrack,
			data.NotTenureTrack,
			data.Professors,
			data.AssociateProfessors,
			data.AssistantProfessors,
			data.Instructors,
			data.AmericanIndian,
			data.Asian,
			data.Black,
			data.Hispanic,
			data.White,
			data.TwoOrMore,
			data.NonresidentAlien,
			strconv.Itoa(year),
		}
		result = append(result, row)
	}

	return result
}

func TransformFinance(records [][]string, year int) [][]string {
	// Filter out X-prefixed columns and rename
	financeColumnMap := map[string]string{
		"UNITID": "unitid",
		"F2A01":  "total_assets",
		"F2A19":  "total_liabilities",
		"F2A20":  "net_assets",
		"F2C01":  "total_revenues",
		"F2C05":  "tuition_fees_gross",
		"F2C07":  "tuition_fees_net",
		"F2C12":  "federal_grants_contracts",
		"F2C13":  "state_grants_contracts",
		"F2C15":  "private_gifts_grants_contracts",
		"F2D01":  "total_expenses",
		"F2D02":  "instruction_total",
		"F2D03":  "research_total",
		"F2D04":  "public_service_total",
		"F2D05":  "academic_support_total",
		"F2H01":  "endowment_assets_boy",
		"F2H02":  "endowment_assets_eoy",
		// Add more columns as needed
	}

	result := extractColumns(records, financeColumnMap)

	// Add year column
	if len(result) > 0 {
		result[0] = append(result[0], "year")
		for i := 1; i < len(result); i++ {
			result[i] = append(result[i], strconv.Itoa(year))
		}
	}

	return result
}

func TransformAdmissions(records [][]string, year int) [][]string {
	columnMap := map[string]string{
		"UNITID":  "unitid",
		"APPLCN":  "applicants",
		"ADMSSN":  "admitted",
		"ENRLT":   "enrolled",
		"SATMT25": "sat_math_25th",
		"SATMT75": "sat_math_75th",
		"ACTCM25": "act_25th_percentile",
		"ACTCM75": "act_75th_percentile",
	}

	result := extractColumns(records, columnMap)

	if len(result) > 0 {
		result[0] = append(result[0], "acceptance_rate", "yield_rate", "year")

		applIdx := 1 // applicants
		admiIdx := 2 // admitted
		enrlIdx := 3 // enrolled

		for i := 1; i < len(result); i++ {
			applicants, _ := strconv.ParseFloat(result[i][applIdx], 64)
			admitted, _ := strconv.ParseFloat(result[i][admiIdx], 64)
			enrolled, _ := strconv.ParseFloat(result[i][enrlIdx], 64)

			acceptanceRate := ""
			yieldRate := ""

			if applicants > 0 {
				acceptanceRate = fmt.Sprintf("%.2f", (admitted/applicants)*100)
			}
			if admitted > 0 {
				yieldRate = fmt.Sprintf("%.2f", (enrolled/admitted)*100)
			}

			result[i] = append(result[i], acceptanceRate, yieldRate, strconv.Itoa(year))
		}
	}

	return result
}

func runIpedsScript() {
	year := 2023
	fetcher := NewIPEDSFetcher(year)

	fmt.Println("Fetching IPEDS data...")

	// Institutions
	fmt.Println("\n=== Institutions ===")
	institutionsRaw, err := fetcher.FetchInstitutions()
	if err == nil {
		institutions := TransformInstitutions(institutionsRaw)
		if err := writeCSV("ipeds_institutions.csv", institutions); err != nil {
			fmt.Printf("✗ Failed to write institutions: %v\n", err)
		} else {
			fmt.Printf("✓ Saved %d institutions\n", len(institutions)-1)
		}
	}

	// Enrollment
	fmt.Println("\n=== Enrollment ===")
	enrollmentRaw, err := fetcher.FetchEnrollment()
	if err == nil {
		enrollment := TransformEnrollment(enrollmentRaw, year)
		if err := writeCSV("ipeds_enrollment.csv", enrollment); err != nil {
			fmt.Printf("✗ Failed to write enrollment: %v\n", err)
		} else {
			fmt.Printf("✓ Saved %d enrollment records\n", len(enrollment)-1)
		}
	}

	// Staff
	fmt.Println("\n=== Staff ===")
	staffRaw, err := fetcher.FetchStaff()
	if err == nil {
		staff := TransformStaff(staffRaw, year)
		if err := writeCSV("ipeds_staff.csv", staff); err != nil {
			fmt.Printf("✗ Failed to write staff: %v\n", err)
		} else {
			fmt.Printf("✓ Saved %d staff records\n", len(staff)-1)
		}
	}

	// Finance
	fmt.Println("\n=== Finance ===")
	financeRaw, err := fetcher.FetchFinance()
	if err == nil {
		finance := TransformFinance(financeRaw, year)
		if err := writeCSV("ipeds_finance.csv", finance); err != nil {
			fmt.Printf("✗ Failed to write finance: %v\n", err)
		} else {
			fmt.Printf("✓ Saved %d finance records\n", len(finance)-1)
		}
	}

	// Admissions
	fmt.Println("\n=== Admissions ===")
	admissionsRaw, err := fetcher.FetchAdmissions()
	if err == nil {
		admissions := TransformAdmissions(admissionsRaw, year)
		if err := writeCSV("ipeds_admissions.csv", admissions); err != nil {
			fmt.Printf("✗ Failed to write admissions: %v\n", err)
		} else {
			fmt.Printf("✓ Saved %d admission records\n", len(admissions)-1)
		}
	}

	fmt.Println("\n✓ All data exported to CSV files")
}
