package main

import (
	"encoding/csv"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// Scholarships students apply for themselves (DAAD, Chevening, Erasmus Mundus, ...), curated in
// backup/scholarships.csv and served by destination country and the student's nationality.
// Eligibility rules and deadlines change every year, so entries link to the official page.
//
// Columns: id,name,provider,destination_countries,levels,eligible_nationalities,covers,
// application_window,official_url,verified,notes
//
//	destination_countries: ISO alpha-2 codes ';'-separated, "EU" for any EU member state, "*" for any
//	eligible_nationalities: ISO codes, "*" for (nearly) all, "developing" for developing countries,
//	                        "!XX" to exclude a country, "!EEA" to exclude EU/EEA nationals
//
// A programme whose application_window is "discontinued" is kept for the record but not served.
const scholarshipsFile = "scholarships.csv"

var euMembers = map[string]bool{
	"AT": true, "BE": true, "BG": true, "HR": true, "CY": true, "CZ": true, "DK": true, "EE": true,
	"FI": true, "FR": true, "DE": true, "GR": true, "HU": true, "IE": true, "IT": true, "LV": true,
	"LT": true, "LU": true, "MT": true, "NL": true, "PL": true, "PT": true, "RO": true, "SK": true,
	"SI": true, "ES": true, "SE": true,
}

// EEA = EU members plus Iceland, Liechtenstein and Norway.
func inEEA(country string) bool {
	return euMembers[country] || country == "IS" || country == "LI" || country == "NO"
}

type scholarship struct {
	ID                    string   `json:"id"`
	Name                  string   `json:"name"`
	Provider              string   `json:"provider"`
	Destinations          []string `json:"destinations"`
	Levels                []string `json:"levels"`
	EligibleNationalities []string `json:"eligible_nationalities"`
	Covers                string   `json:"covers"`
	ApplicationWindow     string   `json:"application_window"`
	URL                   string   `json:"url"`
	Verified              bool     `json:"verified"`
	Notes                 string   `json:"notes"`
	// "eligible", "check" (no nationality given, or a rule like "developing countries"), set per request
	Eligibility string `json:"eligibility,omitempty"`
}

var scholarshipCache struct {
	sync.Mutex
	modTime time.Time
	items   []scholarship
}

func splitCodes(s string) []string {
	var out []string
	for _, p := range strings.Split(s, ";") {
		if p = strings.TrimSpace(p); p != "" {
			out = append(out, strings.ToUpper(p))
		}
	}
	return out
}

func loadScholarships() ([]scholarship, error) {
	path := filepath.Join(getRootDirPath(BACKUP_DIR), scholarshipsFile)
	info, err := os.Stat(path)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	scholarshipCache.Lock()
	defer scholarshipCache.Unlock()
	if info.ModTime().Equal(scholarshipCache.modTime) {
		return scholarshipCache.items, nil
	}

	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	records, err := csv.NewReader(f).ReadAll()
	if err != nil {
		return nil, err
	}

	var items []scholarship
	for i, r := range records {
		if i == 0 || len(r) < 11 {
			continue
		}
		items = append(items, scholarship{
			ID: r[0], Name: r[1], Provider: r[2],
			Destinations:          splitCodes(r[3]),
			Levels:                strings.Split(strings.ToLower(r[4]), ";"),
			EligibleNationalities: splitCodes(r[5]),
			Covers:                r[6], ApplicationWindow: r[7], URL: r[8],
			Verified: strings.EqualFold(strings.TrimSpace(r[9]), "yes"),
			Notes:    r[10],
		})
	}
	scholarshipCache.modTime, scholarshipCache.items = info.ModTime(), items
	return items, nil
}

func (s scholarship) goesTo(country string) bool {
	for _, d := range s.Destinations {
		if d == "*" || d == country || (d == "EU" && euMembers[country]) {
			return true
		}
	}
	return false
}

// eligibilityFor returns "eligible", "check" or "" (not eligible).
func (s scholarship) eligibilityFor(nationality string) string {
	if nationality == "" {
		return "check"
	}
	result := ""
	for _, n := range s.EligibleNationalities {
		switch {
		case n == "!"+nationality, n == "!EEA" && inEEA(nationality):
			return ""
		case n == "!EEA":
			result = "eligible" // open to everyone outside the EEA
		case n == nationality || n == "*":
			result = "eligible"
		case n == "DEVELOPING" && result == "":
			result = "check"
		}
	}
	return result
}

// getExplorerScholarships: GET /explorer/scholarships?country=DE&nationality=PK&level=phd
func getExplorerScholarships(w http.ResponseWriter, r *http.Request) {
	items, err := loadScholarships()
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to load scholarships", err)
		return
	}
	country := strings.ToUpper(strings.TrimSpace(r.URL.Query().Get("country")))
	nationality := strings.ToUpper(strings.TrimSpace(r.URL.Query().Get("nationality")))
	level := strings.ToLower(strings.TrimSpace(r.URL.Query().Get("level")))

	out := []scholarship{}
	for _, s := range items {
		if strings.EqualFold(strings.TrimSpace(s.ApplicationWindow), "discontinued") {
			continue
		}
		if country != "" && !s.goesTo(country) {
			continue
		}
		if level != "" && !strings.Contains(";"+strings.Join(s.Levels, ";")+";", ";"+level+";") {
			continue
		}
		e := s.eligibilityFor(nationality)
		if e == "" {
			continue
		}
		s.Eligibility = e
		out = append(out, s)
	}
	writeJSON(w, http.StatusOK, out)
}
