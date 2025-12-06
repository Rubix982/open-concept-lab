package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
)

// SearchRequest represents a faculty search request
type SearchRequest struct {
	Query   string                 `json:"query"`
	Limit   int                    `json:"limit"`
	Filters map[string]interface{} `json:"filters,omitempty"`
}

// SearchResult represents a single search result
type SearchResult struct {
	Score    float64                `json:"score"`
	Metadata map[string]interface{} `json:"metadata"`
}

// searchFacultyByResearch handles semantic search for faculty
func searchFacultyByResearch(w http.ResponseWriter, r *http.Request) {
	logger.Printf("[HANDLER] %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)

	// Parse request body
	var req SearchRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate query
	if req.Query == "" {
		http.Error(w, "Query is required", http.StatusBadRequest)
		return
	}

	// Set default limit
	if req.Limit == 0 {
		req.Limit = 10
	}

	logger.Infof("Searching for: '%s' (limit: %d)", req.Query, req.Limit)

	// Find Python and search script
	pythonCmd := "python3"
	if _, err := exec.LookPath(pythonCmd); err != nil {
		pythonCmd = "python"
		if _, err := exec.LookPath(pythonCmd); err != nil {
			http.Error(w, "Python not available", http.StatusInternalServerError)
			return
		}
	}

	// Find research service directory
	researchDir := "research_service"
	if _, err := os.Stat(researchDir); os.IsNotExist(err) {
		researchDir = filepath.Join("server", "research_service")
		if _, err := os.Stat(researchDir); os.IsNotExist(err) {
			http.Error(w, "Research service not found", http.StatusInternalServerError)
			return
		}
	}

	searchScript := filepath.Join(researchDir, "search_api.py")

	// Prepare input JSON
	inputJSON, err := json.Marshal(req)
	if err != nil {
		http.Error(w, "Failed to prepare search request", http.StatusInternalServerError)
		return
	}

	// Run Python search
	cmd := exec.Command(pythonCmd, searchScript)
	cmd.Dir = researchDir
	cmd.Stdin = bytes.NewReader(inputJSON)

	// Set environment variables
	cmd.Env = append(os.Environ(),
		fmt.Sprintf("POSTGRES_HOST=%s", os.Getenv("POSTGRES_HOST")),
		fmt.Sprintf("POSTGRES_PORT=%s", os.Getenv("POSTGRES_PORT")),
		fmt.Sprintf("POSTGRES_USER=%s", os.Getenv("POSTGRES_USER")),
		fmt.Sprintf("POSTGRES_PASSWORD=%s", os.Getenv("POSTGRES_PASSWORD")),
		fmt.Sprintf("POSTGRES_DB_NAME=%s", os.Getenv("POSTGRES_DB_NAME")),
		fmt.Sprintf("QDRANT_HOST=%s", os.Getenv("QDRANT_HOST")),
		fmt.Sprintf("QDRANT_PORT=%s", os.Getenv("QDRANT_PORT")),
	)

	// Execute and capture output
	output, err := cmd.CombinedOutput()
	if err != nil {
		logger.Errorf("Search failed: %v\nOutput: %s", err, string(output))
		http.Error(w, "Search failed", http.StatusInternalServerError)
		return
	}

	// Parse results
	var results []SearchResult
	if err := json.Unmarshal(output, &results); err != nil {
		logger.Errorf("Failed to parse search results: %v", err)
		http.Error(w, "Failed to parse results", http.StatusInternalServerError)
		return
	}

	logger.Infof("Found %d results for query: '%s'", len(results), req.Query)

	// Return results
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(results)
}

func fetchAllUniversitiesWithCoordinates() ([]byte, error) {
	db, err := GetDB()
	if err != nil {
		return nil, fmt.Errorf("cannot get DB: %w", err)
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

func fetchUniversitySummary(r *http.Request) ([]byte, error) {
	db, err := GetDB()
	if err != nil {
		return nil, fmt.Errorf("cannot get DB: %w", err)
	}

	// Extract the "country" name from the JSON request body
	var reqBody struct {
		Country string `json:"country"`
		Limit   int    `json:"limit"`
		Offset  int    `json:"offset"`
	}
	if err := json.NewDecoder(r.Body).Decode(&reqBody); err != nil {
		return nil, fmt.Errorf("failed to decode request body: %w", err)
	}
	country := reqBody.Country
	limit := reqBody.Limit
	offset := reqBody.Offset
	if country == "" {
		return nil, fmt.Errorf("country parameter is required")
	}

	// Now, we can query the database for the university with this country
	query := `SELECT * FROM university_summary_view usv WHERE usv.country = $1 LIMIT $2 OFFSET $3;`
	rows, err := db.Query(query, country, limit, offset)
	if err != nil {
		return nil, err
	}

	defer rows.Close()

	columns, err := rows.Columns()
	if err != nil {
		return nil, err
	}

	var results []map[string]any
	for rows.Next() {
		// Create a slice of interface to hold the column values
		values := make([]any, len(columns))
		valuePtrs := make([]any, len(columns))
		for i := range columns {
			valuePtrs[i] = &values[i]
		}

		if err := rows.Scan(valuePtrs...); err != nil {
			return nil, err
		}

		mapResult := make(map[string]any)
		for i, col := range columns {
			val := values[i]
			b, ok := val.([]byte)
			if !ok {
				mapResult[col] = val
				continue
			}

			var jsonVal any
			if err := json.Unmarshal(b, &jsonVal); err == nil {
				mapResult[col] = jsonVal
				continue
			}

			mapResult[col] = string(b)
		}
		results = append(results, mapResult)
	}

	// Now, we need to get the stats object for this university
	jsonData, err := json.Marshal(results)
	if err != nil {
		return nil, err
	}
	return jsonData, nil
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
	summary, err := fetchUniversitySummary(r)
	if err != nil {
		logger.Errorf("Failed to fetch university summary: %v", err)
		http.Error(w, "Failed to fetch university summary", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(summary)
}

func fetchTopUniversitiesSummary(limit int) ([]byte, error) {
	db, err := GetDB()
	if err != nil {
		return nil, fmt.Errorf("cannot get DB: %w", err)
	}

	// Top US universities from out.txt (complete list of 110 universities)
	topUniversities := []string{
		"Massachusetts Institute of Technology",
		"Carnegie Mellon University",
		"Stanford University",
		"University of California--Berkeley",
		"University of Illinois--Urbana-Champaign",
		"Georgia Institute of Technology",
		"Cornell University",
		"Princeton University",
		"University of Texas--Austin",
		"University of Washington",
		"University of Michigan--Ann Arbor",
		"California Institute of Technology",
		"Columbia University",
		"University of California--San Diego",
		"University of Wisconsin--Madison",
		"University of California--Los Angeles",
		"University of Maryland--College Park",
		"University of Pennsylvania",
		"Harvard University",
		"Purdue University--West Lafayette",
		"Johns Hopkins University",
		"University of Massachusetts--Amherst",
		"University of Southern California",
		"Yale University",
		"Duke University",
		"Rice University",
		"Brown University",
		"New York University",
		"Northeastern University",
		"Northwestern University",
		"University of California--Irvine",
		"University of California--Santa Barbara",
		"University of Chicago",
		"University of North Carolina--Chapel Hill",
		"Ohio State University",
		"University of Minnesota--Twin Cities",
		"University of Virginia",
		"Virginia Tech",
		"Arizona State University",
		"Pennsylvania State University--University Park",
		"Texas A&M University--College Station",
		"University of California--Davis",
		"University of Colorado--Boulder",
		"Rutgers University--New Brunswick",
		"Boston University",
		"Dartmouth College",
		"Stony Brook University--SUNY",
		"University of Florida",
		"Vanderbilt University",
		"Washington University in St. Louis",
		"Indiana University--Bloomington",
		"North Carolina State University",
		"University of Pittsburgh",
		"Michigan State University",
		"University of California--Riverside",
		"University of California--Santa Cruz",
		"University of Illinois Chicago",
		"University of Notre Dame",
		"University of Rochester",
		"University of Utah",
		"Tufts University",
		"University of Arizona",
		"University of Texas--Dallas",
		"George Mason University",
		"Iowa State University",
		"Oregon State University",
		"Rensselaer Polytechnic Institute",
		"Syracuse University",
		"University at Buffalo--SUNY",
		"University of Central Florida",
		"Case Western Reserve University",
		"Georgetown University",
		"George Washington University",
		"Rochester Institute of Technology",
		"Toyota Technological Institute at Chicago",
		"University of Delaware",
		"University of Iowa",
		"University of Oregon",
		"William & Mary",
		"Clemson University",
		"Emory University",
		"New Jersey Institute of Technology",
		"Stevens Institute of Technology",
		"University of Georgia",
		"University of Maryland, Baltimore County",
		"University of Nebraska--Lincoln",
		"University of Tennessee--Knoxville",
		"Auburn University",
		"Colorado School of Mines",
		"Drexel University",
		"Florida State University",
		"University of Connecticut",
		"University of Kansas",
		"Binghamton University--SUNY",
		"Colorado State University",
		"Illinois Institute of Technology",
		"Lehigh University",
		"University of North Carolina--Charlotte",
		"University of South Florida",
		"University of Texas--Arlington",
		"Washington State University",
		"Worcester Polytechnic Institute",
		"Brandeis University",
		"Kansas State University",
		"Naval Postgraduate School",
		"Temple University",
		"University of California--Merced",
		"University of Kentucky",
		"University of New Mexico",
		"Brigham Young University",
	}

	// Build query with ILIKE patterns
	query := `
		SELECT * FROM university_summary_view usv 
		WHERE usv.country = 'United States' 
		AND (
	`

	// Add ILIKE conditions for each university
	params := []interface{}{limit}
	for i, uni := range topUniversities {
		if i > 0 {
			query += " OR "
		}
		query += fmt.Sprintf("usv.institution ILIKE $%d", i+1)
		params = append([]interface{}{"%" + uni + "%"}, params...)
	}

	query += ") LIMIT $" + fmt.Sprintf("%d", len(topUniversities)+1) + ";"

	rows, err := db.Query(query, params...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	// Same result processing as fetchUniversitySummary
	columns, err := rows.Columns()
	if err != nil {
		return nil, err
	}

	var results []map[string]any
	for rows.Next() {
		values := make([]any, len(columns))
		valuePtrs := make([]any, len(columns))
		for i := range columns {
			valuePtrs[i] = &values[i]
		}

		if err := rows.Scan(valuePtrs...); err != nil {
			return nil, err
		}

		mapResult := make(map[string]any)
		for i, col := range columns {
			val := values[i]
			b, ok := val.([]byte)
			if !ok {
				mapResult[col] = val
				continue
			}

			var jsonVal any
			if err := json.Unmarshal(b, &jsonVal); err == nil {
				mapResult[col] = jsonVal
				continue
			}

			mapResult[col] = string(b)
		}
		results = append(results, mapResult)
	}

	jsonData, err := json.Marshal(results)
	if err != nil {
		return nil, err
	}
	return jsonData, nil
}

func getTopUniversitiesSummary(w http.ResponseWriter, r *http.Request) {
	logger.Printf("[HANDLER] %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)

	// Get limit from query param, default to 100
	limit := 100
	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if parsedLimit, err := strconv.Atoi(limitStr); err == nil && parsedLimit > 0 {
			limit = parsedLimit
		}
	}

	summary, err := fetchTopUniversitiesSummary(limit)
	if err != nil {
		logger.Errorf("Failed to fetch top universities: %v", err)
		http.Error(w, "Failed to fetch top universities", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(summary)
}
