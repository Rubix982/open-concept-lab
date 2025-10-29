package main

import "net/http"

func helloWorld(w http.ResponseWriter, r *http.Request) {
	logger.Printf("[HANDLER] %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"message":"Hello, world!"}`))
}

func fetchAllUniversitiesWithCoordinates() ([]byte, error) {
	db, err := getPostgresConnection()
	if err != nil {
		return nil, err
	}

	query := `
	    SELECT institution, longitude, latitude, city, region, country
		FROM universities;
	`
	var result []byte
	err = db.QueryRow(query).Scan(&result)
	if err != nil {
		return nil, err
	}
	return result, nil
}

func fetchUniversitySummary() ([]byte, error) {
	db, err := getPostgresConnection()
	if err != nil {
		return nil, err
	}

	// First, we need to get the following columns for each entry in the universities table: 1): institution 2) longitude 3) latitude 4) city 5) region 6) country
	// Then, for each row, we need to build a stats object. To build build this object, we need the following fields, 1): total_faculty, 2): top_research_area, 3): total_nsf_funding, 4): nsf_award_count, 5): active_awards
	// Fetching each of these fields is difficult. For example, to get the int64 value for total_faculty, we need to join two tables, the universities (from institution) table to the professors (to affiliation) table, and then count the number of unique professors for that affiliation.
	// To get the top_research_area, we then need to use these distinct list of professors, and then join with the table professor_areas, and get the "AI"
	query := `

	`
	var result []byte
	err = db.QueryRow(query).Scan(&result)
	if err != nil {
		return nil, err
	}
	return result, nil
}

func getAllUniversitiesWithCoordinates(w http.ResponseWriter, r *http.Request) {
	logger.Printf("[HANDLER] %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)
	universities, err := fetchAllUniversitiesWithCoordinates()
	if err != nil {
		logger.Errorf("Failed to fetch universities: %v", err)
		http.Error(w, "Failed to fetch universities", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(universities)
}

func getUniversitySummary(w http.ResponseWriter, r *http.Request) {
	logger.Printf("[HANDLER] %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)
	summary, err := fetchUniversitySummary()
	if err != nil {
		logger.Errorf("Failed to fetch university summary: %v", err)
		http.Error(w, "Failed to fetch university summary", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(summary)
}
